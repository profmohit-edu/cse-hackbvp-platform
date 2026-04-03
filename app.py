import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import time

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="CSE Hackathon Platform", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1lLjkJ2IFxZTbKhJV_KCoTZqD1fKrDN5OT5e1qhe7iCE/edit"

ADMIN_USER = st.secrets.get("admin_username", "admin")
ADMIN_PASS = st.secrets.get("admin_password", "admin123")

BVCOE_CAMPUS_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/3/3c/Bvcoe_main.JPG"
BV_LOGO = "https://upload.wikimedia.org/wikipedia/en/0/0c/Bharati_Vidyapeeth_Deemed_University_logo.png"

WEIGHTS = {
    "Idea Score": 0.20,
    "Innovation": 0.30,
    "Technical": 0.30,
    "Presentation": 0.10,
    "Impact": 0.10
}

SUBMISSION_HEADERS = ["Team Name", "Members", "Domain", "Idea"]
EVALUATION_HEADERS = [
    "Team Name", "Judge", "Idea Score", "Innovation",
    "Technical", "Presentation", "Impact", "Total", "Time"
]

# =========================================================
# SESSION
# =========================================================
if "role" not in st.session_state:
    st.session_state.role = "Guest"

if "judge_name" not in st.session_state:
    st.session_state.judge_name = ""

if "event_end" not in st.session_state:
    st.session_state.event_end = datetime.now() + timedelta(hours=2)

if "winner_shown" not in st.session_state:
    st.session_state.winner_shown = False

if "prev_top_team" not in st.session_state:
    st.session_state.prev_top_team = None

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# =========================================================
# GOOGLE SHEETS
# =========================================================
@st.cache_resource
def connect_workbook():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open_by_url(SHEET_URL)

wb = connect_workbook()

def ensure_worksheet(sheet_name: str, headers: list[str]):
    try:
        ws = wb.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = wb.add_worksheet(title=sheet_name, rows=1000, cols=max(10, len(headers) + 2))

    values = ws.get_all_values()
    if not values:
        ws.append_row(headers)
    else:
        first_row = [str(x).strip() for x in values[0]]
        if first_row != headers:
            ws.clear()
            ws.append_row(headers)
    return ws

sub_sheet = ensure_worksheet("Submissions", SUBMISSION_HEADERS)
eval_sheet = ensure_worksheet("Evaluations", EVALUATION_HEADERS)

# =========================================================
# HELPERS
# =========================================================
def safe_df(records):
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
    return df

def load_submissions():
    return safe_df(sub_sheet.get_all_records())

def load_evaluations():
    return safe_df(eval_sheet.get_all_records())

def normalize_name(text: str) -> str:
    return str(text).strip().lower()

def team_exists(team_name: str) -> bool:
    df = load_submissions()
    if df.empty:
        return False
    return df["Team Name"].astype(str).str.strip().str.lower().eq(normalize_name(team_name)).any()

def append_submission(team_name: str, members: str, domain: str, idea: str):
    sub_sheet.append_row([team_name, members, domain, idea])

def judge_already_scored(team_name: str, judge_name: str) -> bool:
    ev = load_evaluations()
    if ev.empty:
        return False
    ev["Team Name"] = ev["Team Name"].astype(str).str.strip().str.lower()
    ev["Judge"] = ev["Judge"].astype(str).str.strip().str.lower()
    return ((ev["Team Name"] == normalize_name(team_name)) & (ev["Judge"] == normalize_name(judge_name))).any()

def append_evaluation(team_name: str, judge_name: str, idea_score: int, innovation: int, technical: int, presentation: int, impact: int):
    total = round(
        idea_score * WEIGHTS["Idea Score"] +
        innovation * WEIGHTS["Innovation"] +
        technical * WEIGHTS["Technical"] +
        presentation * WEIGHTS["Presentation"] +
        impact * WEIGHTS["Impact"],
        2
    )
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    eval_sheet.append_row([
        team_name,
        normalize_name(judge_name),
        idea_score,
        innovation,
        technical,
        presentation,
        impact,
        total,
        timestamp
    ])
    return total

def get_leaderboard():
    sub = load_submissions()
    ev = load_evaluations()

    if sub.empty:
        return pd.DataFrame()

    if ev.empty:
        result = sub.copy()
        result["Final Score"] = None
        result["Evaluations"] = 0
        return result

    ev["Total"] = pd.to_numeric(ev["Total"], errors="coerce")

    agg = ev.groupby("Team Name", dropna=False).agg(
        Final_Score=("Total", "mean"),
        Evaluations=("Total", "count")
    ).reset_index()

    agg["Final_Score"] = agg["Final_Score"].round(2)
    agg = agg.rename(columns={"Final_Score": "Final Score"})

    df = sub.merge(agg, on="Team Name", how="left")
    df["Evaluations"] = df["Evaluations"].fillna(0).astype(int)
    df = df.sort_values(by=["Final Score", "Evaluations"], ascending=[False, False], na_position="last")
    return df

def generate_certificate_pdf(team_name: str):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("Certificate of Achievement", styles["Title"]))
    story.append(Spacer(1, 24))
    story.append(Paragraph(f"This is to certify that <b>{team_name}</b>", styles["Heading2"]))
    story.append(Spacer(1, 14))
    story.append(Paragraph("has successfully participated in the CSE Hackathon Platform event.", styles["Normal"]))
    story.append(Spacer(1, 14))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_report_pdf(leaderboard_df: pd.DataFrame, evaluation_df: pd.DataFrame):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("CSE Hackathon Platform - Evaluation Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Developed by Mr. Mohit Tiwari", styles["Normal"]))
    story.append(Paragraph("Department of Computer Science and Engineering, Bharati Vidyapeeth’s College of Engineering, Delhi", styles["Normal"]))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Leaderboard", styles["Heading2"]))
    if leaderboard_df.empty:
        story.append(Paragraph("No leaderboard data available.", styles["Normal"]))
    else:
        lb = leaderboard_df[["Team Name", "Domain", "Final Score", "Evaluations"]].copy()
        lb = lb.fillna("")
        data = [lb.columns.tolist()] + lb.values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ]))
        story.append(table)

    story.append(Spacer(1, 18))
    story.append(Paragraph("Judge Breakdown", styles["Heading2"]))
    if evaluation_df.empty:
        story.append(Paragraph("No evaluation data available.", styles["Normal"]))
    else:
        ev = evaluation_df.copy().fillna("")
        data = [ev.columns.tolist()] + ev.values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ]))
        story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer

# =========================================================
# THEME
# =========================================================
st.session_state.dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)

if st.session_state.dark_mode:
    bg = "#0f172a"
    text = "#f1f5f9"
    card_bg = "linear-gradient(135deg, #1e293b, #0f172a)"
else:
    bg = "#ffffff"
    text = "#1e293b"
    card_bg = "linear-gradient(135deg, #f8fafc, #e2e8f0)"

# =========================================================
# STYLE
# =========================================================
st.markdown(f"""
<style>
.main {{
    background-color: {bg};
    color: {text};
}}

.header-card {{
    background: {card_bg};
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    margin-bottom: 20px;
    animation: glow 3s infinite alternate;
}}

@keyframes glow {{
    from {{ box-shadow: 0 0 10px rgba(59,130,246,0.3); }}
    to {{ box-shadow: 0 0 25px rgba(59,130,246,0.7); }}
}}

.banner {{
    background: #2563eb;
    color: white;
    padding: 12px;
    border-radius: 10px;
    text-align: center;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 10px;
}}

.rank-card {{
    padding: 20px;
    border-radius: 16px;
    font-weight: bold;
    text-align: center;
    font-size: 20px;
}}

.gold {{ background: #FFD700; }}
.silver {{ background: #C0C0C0; }}
.bronze {{ background: #CD7F32; }}

.metric-card {{
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    text-align: center;
    background: rgba(255,255,255,0.8);
}}

.live-note {{
    text-align:center;
    font-size:14px;
    opacity:0.8;
}}

div[data-testid="stHorizontalBlock"] > div:has(.hide-sidebar-helper) {{
    display:none;
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown(f"""
<div class="header-card">
    <div style="display:flex; align-items:center; justify-content:center; gap:15px; flex-wrap:wrap;">
        <img src="{BV_LOGO}" width="60">
        <div style="font-size:34px; font-weight:700;">🚀 CSE Hackathon Platform</div>
    </div>

    <div style="text-align:center; margin-top:10px; line-height:1.6;">
        <img src="{BVCOE_CAMPUS_IMAGE}" style="width:100%; max-height:250px; object-fit:cover; border-radius:14px; margin-bottom:12px;">
        <div style="font-size:20px; font-weight:600;">Developed by Mr. Mohit Tiwari</div>
        <div style="font-size:15px;">Assistant Professor, Department of Computer Science and Engineering</div>
        <div style="font-size:15px;">Cybersecurity & AI Research</div>
        <div style="font-size:14px; opacity:0.85;">Bharati Vidyapeeth’s College of Engineering, Delhi</div>
        <div style="font-size:12px; opacity:0.75; margin-top:8px;">Campus image source: Wikimedia Commons</div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN PANEL
# =========================================================
with st.expander("🔐 Login Panel", expanded=False):
    role_select = st.selectbox("Login As", ["Guest", "Admin", "Judge"], key="role_select_box")

    if role_select == "Admin":
        admin_user = st.text_input("Admin Username")
        admin_pass = st.text_input("Admin Password", type="password")
        if st.button("Login as Admin"):
            if admin_user == ADMIN_USER and admin_pass == ADMIN_PASS:
                st.session_state.role = "Admin"
                st.success("Admin logged in.")
                st.rerun()
            else:
                st.error("Invalid credentials.")

    elif role_select == "Judge":
        judge_name = st.text_input("Judge Name")
        if st.button("Login as Judge"):
            if judge_name.strip():
                st.session_state.role = "Judge"
                st.session_state.judge_name = judge_name.strip()
                st.success(f"Judge {judge_name} logged in.")
                st.rerun()
            else:
                st.error("Judge name is required.")

c_role, c_logout = st.columns([5, 1])
with c_role:
    st.caption(f"👤 Logged in as: {st.session_state.role}" + (f" | Judge: {st.session_state.judge_name}" if st.session_state.role == "Judge" else ""))
with c_logout:
    if st.session_state.role != "Guest":
        if st.button("Logout"):
            st.session_state.role = "Guest"
            st.session_state.judge_name = ""
            st.rerun()

# =========================================================
# NAVIGATION
# =========================================================
menu_options = ["🏠 Dashboard", "🏆 Leaderboard", "📺 Live Leaderboard"]

if st.session_state.role == "Admin":
    menu_options += ["📥 Submit", "📤 Bulk Upload", "📄 Certificates", "📊 Reports", "⏲️ Event Control"]

if st.session_state.role == "Judge":
    menu_options += ["🧑‍⚖️ Evaluate"]

menu = st.radio("Navigation", menu_options, horizontal=True)

# =========================================================
# TIMER
# =========================================================
remaining = st.session_state.event_end - datetime.now()

if remaining.total_seconds() > 0:
    total_seconds = int(remaining.total_seconds())
    hours = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    st.markdown(f"<h3 style='text-align:center;'>⏱️ Time Left: {hours}h {mins}m {secs}s</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 style='text-align:center;'>⏱️ Time Over</h3>", unsafe_allow_html=True)

# =========================================================
# DASHBOARD
# =========================================================
if menu == "🏠 Dashboard":
    st.markdown('<div class="banner">🏁 Hackathon Live Dashboard</div>', unsafe_allow_html=True)
    st.info("📢 Evaluation in progress. Judges, please submit scores on time.")

    sub = load_submissions()
    ev = load_evaluations()
    leaderboard = get_leaderboard()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ideas", len(sub))
    c2.metric("Evaluations", len(ev))
    c3.metric("Teams Evaluated", int(leaderboard["Evaluations"].gt(0).sum()) if not leaderboard.empty else 0)
    c4.metric("Top Score", round(leaderboard.iloc[0]["Final Score"], 2) if not leaderboard.empty and pd.notna(leaderboard.iloc[0]["Final Score"]) else 0)

    if not leaderboard.empty:
        st.markdown("### Current Top 5")
        st.dataframe(leaderboard.head(5), use_container_width=True)

# =========================================================
# SUBMIT
# =========================================================
if menu == "📥 Submit":
    if st.session_state.role != "Admin":
        st.warning("Only admin is allowed.")
        st.stop()

    st.markdown("### Manual Submission")
    team_name = st.text_input("Team Name")
    members = st.text_area("Members")
    domain = st.text_input("Domain")
    idea = st.text_area("Idea")

    if st.button("Submit Entry"):
        if not team_name.strip() or not idea.strip():
            st.error("Team Name and Idea are required.")
        elif team_exists(team_name):
            st.error("This team already exists.")
        else:
            append_submission(team_name, members, domain, idea)
            st.success("Submitted successfully.")
            st.rerun()

# =========================================================
# BULK UPLOAD
# =========================================================
if menu == "📤 Bulk Upload":
    if st.session_state.role != "Admin":
        st.warning("Only admin is allowed.")
        st.stop()

    st.markdown("### ERP-style Bulk Upload")

    template_df = pd.DataFrame(columns=SUBMISSION_HEADERS)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Sheet1")
    buffer.seek(0)

    st.download_button(
        "Download Sample Excel Template",
        data=buffer,
        file_name="hackathon_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    uploaded_file = st.file_uploader("Upload Filled Excel File", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)

            st.dataframe(df_upload, use_container_width=True)

            required_cols = SUBMISSION_HEADERS
            if not all(col in df_upload.columns for col in required_cols):
                st.error(f"Required columns: {required_cols}")
            else:
                if st.button("Upload to Google Sheets"):
                    existing_names = set()
                    current_sub = load_submissions()
                    if not current_sub.empty:
                        existing_names = set(current_sub["Team Name"].astype(str).str.strip().str.lower().tolist())

                    uploaded_count = 0
                    skipped_count = 0

                    for _, row in df_upload.iterrows():
                        team_name = str(row["Team Name"]).strip()
                        if team_name == "" or team_name.lower() in existing_names:
                            skipped_count += 1
                            continue

                        append_submission(
                            team_name,
                            str(row["Members"]),
                            str(row["Domain"]),
                            str(row["Idea"])
                        )
                        existing_names.add(team_name.lower())
                        uploaded_count += 1

                    st.success(f"✅ {uploaded_count} records uploaded successfully.")
                    if skipped_count > 0:
                        st.warning(f"⚠️ {skipped_count} records skipped (duplicate/blank team names).")
                    st.rerun()
        except Exception as e:
            st.error(f"Upload failed: {e}")

# =========================================================
# EVALUATE
# =========================================================
if menu == "🧑‍⚖️ Evaluate":
    if st.session_state.role != "Judge":
        st.warning("Only judges are allowed.")
        st.stop()

    df = load_submissions()
    if df.empty:
        st.warning("No submissions yet.")
        st.stop()

    st.markdown(f"### Judge Panel | Logged in as: {st.session_state.judge_name}")

    team = st.selectbox("Team", df["Team Name"].tolist())

    if judge_already_scored(team, st.session_state.judge_name):
        st.warning("You have already evaluated this team. Re-evaluation is locked.")
        st.stop()

    idea = st.slider("Idea Score", 0, 10, 5)
    innovation = st.slider("Innovation", 0, 10, 5)
    technical = st.slider("Technical", 0, 10, 5)
    presentation = st.slider("Presentation", 0, 10, 5)
    impact = st.slider("Impact", 0, 10, 5)

    total = round(
        idea * WEIGHTS["Idea Score"] +
        innovation * WEIGHTS["Innovation"] +
        technical * WEIGHTS["Technical"] +
        presentation * WEIGHTS["Presentation"] +
        impact * WEIGHTS["Impact"],
        2
    )

    st.info(f"Weighted Score Preview: {total}")

    if st.button("Submit Score"):
        final_total = append_evaluation(
            team,
            st.session_state.judge_name,
            idea,
            innovation,
            technical,
            presentation,
            impact
        )
        st.success(f"Score submitted. Final weighted score: {final_total}")
        st.rerun()

# =========================================================
# LEADERBOARD
# =========================================================
if menu == "🏆 Leaderboard":
    df = get_leaderboard()

    if df.empty:
        st.warning("No scores yet.")
    else:
        st.markdown("### Top 3 Teams")
        top3 = df.head(3)
        cols = st.columns(3)
        colors = ["gold", "silver", "bronze"]

        for i in range(len(top3)):
            with cols[i]:
                score = top3.iloc[i]["Final Score"]
                score_text = round(score, 2) if pd.notna(score) else "NA"
                st.markdown(f"""
                <div class="rank-card {colors[i]}">
                    Rank {i+1}<br>
                    {top3.iloc[i]["Team Name"]}<br>
                    Score: {score_text}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("### Full Rankings")
        st.dataframe(df, use_container_width=True)

        st.markdown("### 👨‍⚖️ Judge Breakdown")
        st.dataframe(load_evaluations(), use_container_width=True)

        if remaining.total_seconds() <= 0 and not st.session_state.winner_shown:
            st.session_state.winner_shown = True
            st.balloons()
            st.success(f"🏆 Winner: {df.iloc[0]['Team Name']}")

# =========================================================
# LIVE LEADERBOARD
# =========================================================
if menu == "📺 Live Leaderboard":
    st.markdown('<div class="banner">🎥 Projector Mode | Press F11 for browser fullscreen</div>', unsafe_allow_html=True)
    st.caption("🔄 Auto-refresh every 5 seconds")

    df = get_leaderboard()

    if df.empty:
        st.warning("Waiting for scores...")
    else:
        top_team = df.iloc[0]["Team Name"]

        if st.session_state.prev_top_team != top_team:
            st.session_state.prev_top_team = top_team
            st.markdown("""
            <audio autoplay>
                <source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg">
            </audio>
            """, unsafe_allow_html=True)

        st.markdown("## 🏆 LIVE HACKATHON LEADERBOARD")

        top3 = df.head(3)
        cols = st.columns(3)
        colors = ["gold", "silver", "bronze"]

        for i in range(len(top3)):
            with cols[i]:
                score = top3.iloc[i]["Final Score"]
                score_text = round(score, 2) if pd.notna(score) else "NA"
                st.markdown(f"""
                <div class="rank-card {colors[i]}">
                    🏅 Rank {i+1}<br>
                    {top3.iloc[i]["Team Name"]}<br>
                    Score: {score_text}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("### Full Rankings")
        st.dataframe(df, use_container_width=True)

        st.markdown("### 👨‍⚖️ Judge-wise Scores")
        st.dataframe(load_evaluations(), use_container_width=True)

        if remaining.total_seconds() <= 0 and not st.session_state.winner_shown:
            st.session_state.winner_shown = True
            st.balloons()
            st.markdown(f"""
            <h1 style='text-align:center; color:gold; font-size:60px;'>
            🏆 WINNER: {df.iloc[0]['Team Name']}
            </h1>
            <audio autoplay>
                <source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" type="audio/mpeg">
            </audio>
            """, unsafe_allow_html=True)

    time.sleep(5)
    st.rerun()

# =========================================================
# CERTIFICATES
# =========================================================
if menu == "📄 Certificates":
    if st.session_state.role != "Admin":
        st.warning("Only admin is allowed.")
        st.stop()

    sub = load_submissions()
    if sub.empty:
        st.warning("No teams available.")
        st.stop()

    team = st.selectbox("Team", sub["Team Name"])

    if st.button("Generate Certificate"):
        pdf_buffer = generate_certificate_pdf(team)
        st.download_button("Download Certificate", pdf_buffer, f"{team}_certificate.pdf", mime="application/pdf")

# =========================================================
# REPORTS
# =========================================================
if menu == "📊 Reports":
    if st.session_state.role != "Admin":
        st.warning("Only admin is allowed.")
        st.stop()

    leaderboard_df = get_leaderboard()
    evaluation_df = load_evaluations()

    st.markdown("### CSV Downloads")

    if not leaderboard_df.empty:
        st.download_button(
            "Download Leaderboard CSV",
            leaderboard_df.to_csv(index=False),
            "leaderboard.csv",
            mime="text/csv"
        )

    if not evaluation_df.empty:
        st.download_button(
            "Download Judge Breakdown CSV",
            evaluation_df.to_csv(index=False),
            "judge_breakdown.csv",
            mime="text/csv"
        )

    st.markdown("### PDF Report")
    pdf_buffer = generate_report_pdf(leaderboard_df, evaluation_df)
    st.download_button(
        "Download PDF Report",
        pdf_buffer,
        "hackathon_report.pdf",
        mime="application/pdf"
    )

# =========================================================
# EVENT CONTROL
# =========================================================
if menu == "⏲️ Event Control":
    if st.session_state.role != "Admin":
        st.warning("Only admin is allowed.")
        st.stop()

    st.markdown("### Event Timer Control")
    minutes = st.number_input("Reset countdown to how many minutes?", min_value=1, max_value=600, value=120)

    if st.button("Reset Timer"):
        st.session_state.event_end = datetime.now() + timedelta(minutes=int(minutes))
        st.session_state.winner_shown = False
        st.success("Timer reset successfully.")
        st.rerun()
