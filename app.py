import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import time

# ================= CONFIG =================
st.set_page_config(page_title="CSE Hackathon Platform", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1lLjkJ2IFxZTbKhJV_KCoTZqD1fKrDN5OT5e1qhe7iCE/edit"

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

WEIGHTS = {
    "Idea": 0.20,
    "Innovation": 0.30,
    "Technical": 0.30,
    "Presentation": 0.10,
    "Impact": 0.10
}

# ================= SESSION =================
if "event_end" not in st.session_state:
    st.session_state.event_end = datetime.now() + timedelta(hours=2)

if "winner_shown" not in st.session_state:
    st.session_state.winner_shown = False

EVENT_END = st.session_state.event_end

# ================= GOOGLE SHEETS =================
@st.cache_resource
def connect():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open_by_url(SHEET_URL)

wb = connect()
sub_sheet = wb.worksheet("Submissions")
eval_sheet = wb.worksheet("Evaluations")

# ================= HELPERS =================
def safe_df(data):
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    return df

def load_sub():
    return safe_df(sub_sheet.get_all_records())

def load_eval():
    return safe_df(eval_sheet.get_all_records())

def get_leaderboard():
    sub = load_sub()
    ev = load_eval()

    if ev.empty:
        return pd.DataFrame()

    total_col = [c for c in ev.columns if c.lower() in ["total","score"]][0]
    ev[total_col] = pd.to_numeric(ev[total_col], errors='coerce')

    agg = ev.groupby("Team Name")[total_col].mean().reset_index()
    agg = agg.rename(columns={total_col:"Final Score"})

    df = sub.merge(agg, on="Team Name", how="left")
    return df.sort_values(by="Final Score", ascending=False)

# ================= DARK MODE =================
dark_mode = st.toggle("🌙 Dark Mode", value=False)

if dark_mode:
    bg = "#0f172a"
    text = "#f1f5f9"
else:
    bg = "#ffffff"
    text = "#1e293b"

# ================= STYLE =================
st.markdown(f"""
<style>
body {{ background:{bg}; color:{text}; }}

.header {{
    padding:20px;
    border-radius:15px;
    box-shadow:0 5px 20px rgba(0,0,0,0.15);
    text-align:center;
    margin-bottom:20px;
}}

.banner {{
    background:#2563eb;
    color:white;
    padding:10px;
    border-radius:10px;
    text-align:center;
    font-size:18px;
}}

.card {{
    padding:20px;
    border-radius:15px;
    font-weight:bold;
    text-align:center;
}}

.gold {{background:#FFD700;}}
.silver {{background:#C0C0C0;}}
.bronze {{background:#CD7F32;}}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("""
<div class="header">
<img src="https://upload.wikimedia.org/wikipedia/en/0/0c/Bharati_Vidyapeeth_Deemed_University_logo.png" width="60"><br>
<h2>🚀 CSE Hackathon Platform</h2>
<b>Developed by Mr. Mohit Tiwari</b><br>
Assistant Professor, Department of Computer Science and Engineering<br>
Cybersecurity & AI Research<br>
Bharati Vidyapeeth’s College of Engineering, Delhi
</div>
""", unsafe_allow_html=True)

# ================= NAVIGATION =================
menu = st.radio(
    "Navigation",
    ["🏠 Dashboard","📥 Submit","🧑‍⚖️ Evaluate","🏆 Leaderboard","📄 Certificates"],
    horizontal=True
)

# ================= TIMER =================
remaining = EVENT_END - datetime.now()
if remaining.total_seconds() > 0:
    mins, secs = divmod(int(remaining.total_seconds()), 60)
    st.markdown(f"<h3 style='text-align:center;'>⏱️ {mins}m {secs}s left</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 style='text-align:center;'>⏱️ Time Over</h3>", unsafe_allow_html=True)

# ================= DASHBOARD =================
if menu == "🏠 Dashboard":
    st.markdown('<div class="banner">🏁 Hackathon Live Dashboard</div>', unsafe_allow_html=True)

    sub = load_sub()
    ev = load_eval()

    st.info("📢 Evaluation in progress. Judges please submit scores.")

    c1,c2,c3 = st.columns(3)
    c1.metric("Ideas", len(sub))
    c2.metric("Evaluations", len(ev))
    c3.metric("Teams", ev["Team Name"].nunique() if not ev.empty else 0)

# ================= SUBMIT =================
if menu == "📥 Submit":
    t = st.text_input("Team Name")
    m = st.text_area("Members")
    d = st.text_input("Domain")
    i = st.text_area("Idea")

    if st.button("Submit"):
        sub_sheet.append_row([t,m,d,i])
        st.success("Submitted successfully")

# ================= EVALUATE =================
if menu == "🧑‍⚖️ Evaluate":
    df = load_sub()
    team = st.selectbox("Team", df["Team Name"])

    idea = st.slider("Idea",0,10)
    innovation = st.slider("Innovation",0,10)
    tech = st.slider("Technical",0,10)
    pres = st.slider("Presentation",0,10)
    impact = st.slider("Impact",0,10)

    total = round(
        idea*WEIGHTS["Idea"] +
        innovation*WEIGHTS["Innovation"] +
        tech*WEIGHTS["Technical"] +
        pres*WEIGHTS["Presentation"] +
        impact*WEIGHTS["Impact"],2
    )

    st.write("Total Score:", total)

    if st.button("Submit Score"):
        eval_sheet.append_row([
            team,"Judge",
            idea,innovation,tech,pres,impact,
            total,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
        st.success("Score saved")

# ================= LEADERBOARD =================
if menu == "🏆 Leaderboard":
    df = get_leaderboard()

    if df.empty:
        st.warning("No scores yet")
    else:
        top3 = df.head(3)
        cols = st.columns(3)
        colors = ["gold","silver","bronze"]

        for i in range(len(top3)):
            with cols[i]:
                st.markdown(f"""
                <div class="card {colors[i]}">
                Rank {i+1}<br>
                {top3.iloc[i]["Team Name"]}<br>
                Score: {round(top3.iloc[i]["Final Score"],2)}
                </div>
                """, unsafe_allow_html=True)

        st.dataframe(df, use_container_width=True)

        if remaining.total_seconds() <= 0 and not st.session_state.winner_shown:
            st.session_state.winner_shown = True
            st.balloons()
            st.success(f"🏆 Winner: {df.iloc[0]['Team Name']}")

# ================= CERTIFICATE =================
if menu == "📄 Certificates":
    sub = load_sub()
    team = st.selectbox("Team", sub["Team Name"])

    if st.button("Generate Certificate"):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()

        story = []
        story.append(Paragraph("Certificate of Achievement", styles["Title"]))
        story.append(Paragraph(f"Awarded to {team}", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)

        st.download_button("Download", buffer, f"{team}.pdf")

# ================= AUTO REFRESH =================
time.sleep(5)
st.rerun()
