import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import time

# ================= CONFIG =================
st.set_page_config(page_title="CSE Hackathon Platform", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1lLjkJ2IFxZTbKhJV_KCoTZqD1fKrDN5OT5e1qhe7iCE/edit"

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

SUBMISSION_HEADERS = ["Team Name", "Members", "Domain", "Idea"]
EVALUATION_HEADERS = ["Team Name", "Judge", "Idea Score", "Innovation", "Technical", "Presentation", "Impact", "Total", "Time"]

WEIGHTS = {
    "Idea Score": 0.20,
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

if "event_end" not in st.session_state:
    st.session_state.event_end = datetime.now() + timedelta(hours=2)

if "winner_shown" not in st.session_state:
    st.session_state.winner_shown = False

if "prev_top_team" not in st.session_state:
    st.session_state.prev_top_team = None

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

def ensure_sheet(name, headers):
    try:
        ws = wb.worksheet(name)
    except:
        ws = wb.add_worksheet(title=name, rows=1000, cols=20)

    values = ws.get_all_values()
    if not values or values[0] != headers:
        ws.clear()
        ws.append_row(headers)

    return ws

sub_sheet = ensure_sheet("Submissions", SUBMISSION_HEADERS)
eval_sheet = ensure_sheet("Evaluations", EVALUATION_HEADERS)

# ================= SAFE LOAD =================
def load_sub():
    try:
        return pd.DataFrame(sub_sheet.get_all_records())
    except:
        sub_sheet.clear()
        sub_sheet.append_row(SUBMISSION_HEADERS)
        return pd.DataFrame()

def load_eval():
    try:
        return pd.DataFrame(eval_sheet.get_all_records())
    except:
        eval_sheet.clear()
        eval_sheet.append_row(EVALUATION_HEADERS)
        return pd.DataFrame()

# ================= LEADERBOARD =================
def get_leaderboard():
    sub = load_sub()
    ev = load_eval()

    if ev.empty:
        return pd.DataFrame()

    ev["Total"] = pd.to_numeric(ev["Total"], errors='coerce')
    agg = ev.groupby("Team Name")["Total"].mean().reset_index()
    agg.rename(columns={"Total": "Final Score"}, inplace=True)

    df = sub.merge(agg, on="Team Name", how="left")
    return df.sort_values(by="Final Score", ascending=False)

# ================= HEADER (FIXED) =================
st.markdown("""
<div style="
background: linear-gradient(135deg,#f8fafc,#e2e8f0);
padding:20px;
border-radius:18px;
box-shadow:0 8px 25px rgba(0,0,0,0.15);
text-align:center;
margin-bottom:20px;
">

<img src="https://upload.wikimedia.org/wikipedia/en/0/0c/Bharati_Vidyapeeth_Deemed_University_logo.png" width="60">

<h2>🚀 CSE Hackathon Platform</h2>

<img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Bvcoe_main.JPG"
style="width:100%;max-height:250px;object-fit:cover;border-radius:14px;margin:10px 0;">

<div style="font-size:20px;font-weight:600;">Developed by Mr. Mohit Tiwari</div>
<div>Assistant Professor, CSE Department</div>
<div>Cybersecurity & AI Research</div>
<div>Bharati Vidyapeeth’s College of Engineering, Delhi</div>

<div style="font-size:12px;margin-top:8px;">Image: Wikimedia Commons</div>

</div>
""", unsafe_allow_html=True)

# ================= LOGIN =================
with st.expander("🔐 Login"):
    role = st.selectbox("Login As", ["Guest", "Admin", "Judge"])

    if role == "Admin":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login Admin"):
            if u == ADMIN_USER and p == ADMIN_PASS:
                st.session_state.role = "Admin"
                st.success("Admin logged in")

    if role == "Judge":
        name = st.text_input("Judge Name")
        if st.button("Login Judge"):
            st.session_state.role = "Judge"
            st.session_state.judge_name = name
            st.success(f"Judge {name} logged in")

st.write("Logged in as:", st.session_state.role)

# ================= MENU =================
menu = ["Dashboard", "Leaderboard"]

if st.session_state.role == "Admin":
    menu += ["Submit", "Bulk Upload", "Certificates", "Control"]

if st.session_state.role == "Judge":
    menu += ["Evaluate"]

choice = st.radio("Navigation", menu, horizontal=True)

# ================= TIMER =================
remaining = st.session_state.event_end - datetime.now()
st.write("⏱️ Time Left:", str(remaining).split(".")[0])

# ================= DASHBOARD =================
if choice == "Dashboard":
    st.info("Evaluation in progress")

    sub = load_sub()
    ev = load_eval()

    c1, c2 = st.columns(2)
    c1.metric("Submissions", len(sub))
    c2.metric("Evaluations", len(ev))

# ================= SUBMIT =================
if choice == "Submit":
    t = st.text_input("Team")
    m = st.text_area("Members")
    d = st.text_input("Domain")
    i = st.text_area("Idea")

    if st.button("Submit"):
        sub_sheet.append_row([t,m,d,i])
        st.success("Submitted")

# ================= BULK =================
if choice == "Bulk Upload":
    file = st.file_uploader("Upload Excel")

    if file:
        df = pd.read_excel(file)
        st.dataframe(df)

        if st.button("Upload"):
            for _, r in df.iterrows():
                sub_sheet.append_row(r.tolist())
            st.success("Uploaded")

# ================= EVALUATE =================
if choice == "Evaluate":
    df = load_sub()
    team = st.selectbox("Team", df["Team Name"])

    ev = load_eval()
    if not ev.empty and ((ev["Team Name"] == team) & (ev["Judge"] == st.session_state.judge_name)).any():
        st.warning("Already evaluated")
        st.stop()

    idea = st.slider("Idea",0,10)
    innovation = st.slider("Innovation",0,10)
    tech = st.slider("Technical",0,10)
    pres = st.slider("Presentation",0,10)
    impact = st.slider("Impact",0,10)

    total = round(idea*0.2+innovation*0.3+tech*0.3+pres*0.1+impact*0.1,2)

    if st.button("Submit Score"):
        eval_sheet.append_row([team, st.session_state.judge_name, idea, innovation, tech, pres, impact, total, str(datetime.now())])
        st.success("Score submitted")

# ================= LEADERBOARD =================
if choice == "Leaderboard":
    df = get_leaderboard()

    if not df.empty:
        st.dataframe(df)

        top = df.iloc[0]["Team Name"]
        if st.session_state.prev_top_team != top:
            st.session_state.prev_top_team = top
            st.balloons()

# ================= CERTIFICATE =================
if choice == "Certificates":
    df = load_sub()
    team = st.selectbox("Team", df["Team Name"])

    if st.button("Generate"):
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()

        story = [
            Paragraph("Certificate of Achievement", styles["Title"]),
            Spacer(1,20),
            Paragraph(f"Awarded to {team}", styles["Normal"])
        ]

        doc.build(story)
        buf.seek(0)

        st.download_button("Download", buf, f"{team}.pdf")

# ================= CONTROL =================
if choice == "Control":
    mins = st.number_input("Reset Timer (minutes)", value=120)
    if st.button("Reset"):
        st.session_state.event_end = datetime.now() + timedelta(minutes=mins)
        st.success("Timer Reset")

# ================= AUTO REFRESH =================
time.sleep(5)
st.rerun()
