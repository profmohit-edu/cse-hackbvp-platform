import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from streamlit_autorefresh import st_autorefresh

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

# ================= FULLSCREEN CSS =================
st.markdown("""
<style>
[data-testid="stSidebar"] {display:none;}
.card {padding:20px;border-radius:15px;text-align:center;font-size:22px;font-weight:bold;margin:10px;}
.gold {background:#FFD700; animation: pulse 1.5s infinite;}
.silver {background:#C0C0C0;}
.bronze {background:#CD7F32;}
@keyframes pulse {0%{opacity:1;}50%{opacity:0.6;}100%{opacity:1;}}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("""
<div style='text-align:center; line-height:1.6; margin-bottom:10px;'>
    <h1 style='margin-bottom:5px;'>🚀 CSE Hackathon Platform</h1>

    <h3 style='margin:0; color:#333;'>
        Developed by <b>Mr. Mohit Tiwari</b>
    </h3>

    <p style='margin:0; font-size:16px;'>
        Assistant Professor, Department of Computer Science and Engineering
    </p>

    <p style='margin:0; font-size:15px;'>
        Cybersecurity & AI Research
    </p>

    <p style='margin:0; font-size:15px;'>
        Bharati Vidyapeeth’s College of Engineering, Delhi
    </p>
</div>
<hr>
""", unsafe_allow_html=True)

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
    "Dashboard","Submit","Evaluate Panel",
    "Leaderboard","Live Leaderboard","Certificates"
])

# ================= LEADERBOARD FUNCTION =================
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

# ================= LIVE LEADERBOARD =================
if menu == "Live Leaderboard":

    st_autorefresh(interval=4000, key="live")

    # ⏱️ TIMER
    remaining = EVENT_END - datetime.now()
    mins, secs = divmod(int(remaining.total_seconds()), 60)

    st.markdown(f"<h2 style='text-align:center;'>⏱️ {mins}m {secs}s left</h2>", unsafe_allow_html=True)

    df = get_leaderboard()

    if df.empty:
        st.warning("Waiting for scores...")
        st.stop()

    top_team = df.iloc[0]["Team Name"]

    # 🔊 SOUND ALERT
    if st.session_state.prev_top != top_team:
        st.audio("https://www.soundjay.com/buttons/sounds/button-3.mp3")
        st.session_state.prev_top = top_team

    # 🏆 WINNER POPUP
    if remaining.total_seconds() <= 0 and not st.session_state.winner_shown:
        st.session_state.winner_shown = True
        st.markdown(f"""
        <h1 style='text-align:center;color:gold;font-size:60px;'>
        🏆 WINNER: {top_team}
        </h1>
        """, unsafe_allow_html=True)
        st.balloons()
        st.audio("https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3")

    # 🥇 TOP 3
    top3 = df.head(3)
    cols = st.columns(3)
    colors = ["gold","silver","bronze"]

    for i in range(len(top3)):
        with cols[i]:
            st.markdown(f"""
            <div class='card {colors[i]}'>
            🏅 Rank {i+1}<br>
            {top3.iloc[i]["Team Name"]}<br>
            Score: {round(top3.iloc[i]["Final Score"],2)}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### 📊 Full Rankings")
    st.dataframe(df, use_container_width=True)

    # 👨‍⚖️ JUDGE BREAKDOWN
    st.markdown("### 👨‍⚖️ Judge-wise Scores")
    ev = load_eval()
    if not ev.empty:
        st.dataframe(ev)

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
