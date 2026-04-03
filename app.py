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

EVENT_END = datetime.now() + timedelta(hours=2)

WEIGHTS = {
    "Idea": 0.20,
    "Innovation": 0.30,
    "Technical": 0.30,
    "Presentation": 0.10,
    "Impact": 0.10
}

# ================= SESSION =================
if "role" not in st.session_state:
    st.session_state.role = "Guest"
if "judge_name" not in st.session_state:
    st.session_state.judge_name = ""
if "prev_top" not in st.session_state:
    st.session_state.prev_top = None
if "winner_shown" not in st.session_state:
    st.session_state.winner_shown = False

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
    bg_color = "#0f172a"
    text_color = "#f1f5f9"
    card_bg = "linear-gradient(135deg, #1e293b, #0f172a)"
else:
    bg_color = "#ffffff"
    text_color = "#1e293b"
    card_bg = "linear-gradient(135deg, #f8fafc, #e2e8f0)"

# ================= GLOBAL STYLE =================
st.markdown(f"""
<style>
[data-testid="stSidebar"] {{display:none;}}

body {{
    background-color: {bg_color};
    color: {text_color};
}}

.header-card {{
    background: {card_bg};
    padding: 25px;
    border-radius: 18px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    margin-bottom: 20px;
    animation: glow 3s infinite alternate;
}}

@keyframes glow {{
    from {{ box-shadow: 0 0 10px rgba(59,130,246,0.3); }}
    to {{ box-shadow: 0 0 25px rgba(59,130,246,0.7); }}
}}

.center {{
    text-align:center;
}}

.card {{
    padding:20px;
    border-radius:15px;
    font-size:22px;
    font-weight:bold;
}}

.gold {{background:#FFD700;}}
.silver {{background:#C0C0C0;}}
.bronze {{background:#CD7F32;}}

.banner {{
    background:#2563eb;
    color:white;
    padding:10px;
    border-radius:10px;
    text-align:center;
    font-size:18px;
}}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("""
<div class="header-card">

<div style="display:flex;align-items:center;justify-content:center;gap:15px;">
<img src="https://upload.wikimedia.org/wikipedia/en/0/0c/Bharati_Vidyapeeth_Deemed_University_logo.png" width="55">
<div style="font-size:34px;font-weight:700;">🚀 CSE Hackathon Platform</div>
</div>

<div class="center" style="margin-top:10px;">
<b>Developed by Mr. Mohit Tiwari</b><br>
Assistant Professor, Department of Computer Science and Engineering<br>
Cybersecurity & AI Research<br>
Bharati Vidyapeeth’s College of Engineering, Delhi
</div>

</div>
""", unsafe_allow_html=True)

# ================= LANDING DASHBOARD =================
st.markdown('<div class="banner">🏁 Hackathon Live Dashboard</div>', unsafe_allow_html=True)

remaining = EVENT_END - datetime.now()
mins, secs = divmod(int(remaining.total_seconds()), 60)

st.markdown(f"<h2 class='center'>⏱️ Time Left: {mins}m {secs}s</h2>", unsafe_allow_html=True)

st.info("📢 Announcement: Evaluation in progress. Judges please submit scores on time.")

# ================= LOGIN =================
st.sidebar.title("Login")

role = st.sidebar.selectbox("Role", ["Guest", "Admin", "Judge"])

if role == "Admin":
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if u == ADMIN_USER and p == ADMIN_PASS:
            st.session_state.role = "Admin"

elif role == "Judge":
    name = st.sidebar.text_input("Judge Name")
    if st.sidebar.button("Login"):
        if name:
            st.session_state.role = "Judge"
            st.session_state.judge_name = name.strip().lower()

menu = st.sidebar.radio("Menu", [
    "Dashboard","Submit","Evaluate","Leaderboard","Certificates"
])

# ================= DASHBOARD =================
if menu == "Dashboard":
    sub = load_sub()
    ev = load_eval()

    c1,c2,c3 = st.columns(3)
    c1.metric("Ideas", len(sub))
    c2.metric("Evaluations", len(ev))
    c3.metric("Teams", ev["Team Name"].nunique() if not ev.empty else 0)

# ================= SUBMIT =================
if menu == "Submit":
    t = st.text_input("Team Name")
    m = st.text_area("Members")
    d = st.text_input("Domain")
    i = st.text_area("Idea")

    if st.button("Submit"):
        sub_sheet.append_row([t,m,d,i])
        st.success("Submitted")

# ================= EVALUATE =================
if menu == "Evaluate":
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

    if st.button("Submit Score"):
        eval_sheet.append_row([
            team,
            st.session_state.judge_name,
            idea,innovation,tech,pres,impact,
            total,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
        st.success("Saved")

# ================= LEADERBOARD =================
if menu == "Leaderboard":
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
if menu == "Certificates":
    sub = load_sub()
    team = st.selectbox("Team", sub["Team Name"])

    if st.button("Generate"):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()

        story = []
        story.append(Paragraph("Certificate of Achievement", styles["Title"]))
        story.append(Paragraph(f"Awarded to {team}", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)

        st.download_button("Download", buffer, f"{team}.pdf")
