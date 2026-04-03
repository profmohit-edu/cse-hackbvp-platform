import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

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
if "role" not in st.session_state:
    st.session_state.role = "Guest"
if "judge_name" not in st.session_state:
    st.session_state.judge_name = ""

# ================= CONNECT =================
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

# ================= SAFE LOAD =================
def safe_df(df):
    if df is None or len(df) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(df)
    df.columns = df.columns.str.strip()
    return df

def load_sub():
    return safe_df(sub_sheet.get_all_records())

def load_eval():
    return safe_df(eval_sheet.get_all_records())

# ================= HEADER =================
st.markdown("""
<h1 style='text-align:center;'>🚀 CSE Hackathon Platform</h1>
<p style='text-align:center;'>
Developed by <b>Mr. Mohit Tiwari</b><br>
Assistant Professor, CSE Department<br>
Bharati Vidyapeeth’s College of Engineering, Delhi
</p>
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
            st.success("Admin logged in")

elif role == "Judge":
    name = st.sidebar.text_input("Judge Name")
    if st.sidebar.button("Login"):
        if name:
            st.session_state.role = "Judge"
            st.session_state.judge_name = name.strip().lower()
            st.success("Judge logged in")

# ================= MENU =================
if st.session_state.role == "Admin":
    menu = st.sidebar.radio("Menu", [
        "Dashboard","Submit","Bulk Upload","Evaluate Panel",
        "Leaderboard","Certificates","Reports"
    ])
elif st.session_state.role == "Judge":
    menu = st.sidebar.radio("Menu", ["Evaluate Panel"])
else:
    menu = st.sidebar.radio("Menu", ["Submit","Leaderboard"])

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.subheader("📊 Dashboard")

    sub = load_sub()
    ev = load_eval()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Ideas", len(sub))

    if ev.empty:
        c2.metric("Total Evaluations", 0)
        c3.metric("Evaluated Teams", 0)
    else:
        c2.metric("Total Evaluations", len(ev))
        if "Team Name" in ev.columns:
            c3.metric("Evaluated Teams", ev["Team Name"].nunique())
        else:
            c3.metric("Evaluated Teams", 0)

# ================= SUBMIT =================
if menu == "Submit":
    st.subheader("Submit Idea")

    t = st.text_input("Team Name")
    m = st.text_area("Members")
    d = st.text_input("Domain")
    i = st.text_area("Idea")

    if st.button("Submit"):
        sub_sheet.append_row([t, m, d, i])
        st.success("Submitted")

# ================= BULK UPLOAD =================
if menu == "Bulk Upload":
    st.subheader("Bulk Upload")

    df_template = pd.DataFrame(columns=["Team Name","Members","Domain","Idea"])
    buffer = BytesIO()
    df_template.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button("Download Template", buffer, "template.xlsx")

    file = st.file_uploader("Upload Excel", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        st.dataframe(df)

        if st.button("Upload"):
            for _, r in df.iterrows():
                sub_sheet.append_row(list(r))
            st.success("Uploaded")

# ================= EVALUATE =================
if menu == "Evaluate Panel":
    st.subheader("Judge Panel")

    df = load_sub()
    ev = load_eval()

    if df.empty:
        st.warning("No submissions yet")
        st.stop()

    team = st.selectbox("Team", df["Team Name"])

    # LOCK CHECK
    judge_col = None
    for col in ev.columns:
        if col.lower() in ["judge", "evaluator"]:
            judge_col = col

    if judge_col:
        if ((ev["Team Name"] == team) &
            (ev[judge_col] == st.session_state.judge_name)).any():
            st.warning("Already evaluated by you")
            st.stop()

    idea = st.slider("Idea",0,10,5)
    innovation = st.slider("Innovation",0,10,5)
    tech = st.slider("Technical",0,10,5)
    pres = st.slider("Presentation",0,10,5)
    impact = st.slider("Impact",0,10,5)

    total = round(
        idea*WEIGHTS["Idea"] +
        innovation*WEIGHTS["Innovation"] +
        tech*WEIGHTS["Technical"] +
        pres*WEIGHTS["Presentation"] +
        impact*WEIGHTS["Impact"], 2
    )

    st.info(f"Score: {total}")

    if st.button("Submit Score"):
        eval_sheet.append_row([
            team,
            st.session_state.judge_name,
            idea, innovation, tech, pres, impact,
            total,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
        st.success("Saved")

# ================= LEADERBOARD =================
if menu == "Leaderboard":
    st.subheader("Leaderboard")

    sub = load_sub()
    ev = load_eval()

    if ev.empty:
        st.warning("No evaluations yet")
        st.stop()

    total_col = None
    for col in ev.columns:
        if col.lower() in ["total", "score"]:
            total_col = col

    if not total_col:
        st.error("Total column missing")
        st.stop()

    ev[total_col] = pd.to_numeric(ev[total_col], errors='coerce')

    agg = ev.groupby("Team Name")[total_col].mean().reset_index()
    df = sub.merge(agg, on="Team Name", how="left")
    df = df.sort_values(by=total_col, ascending=False)

    st.dataframe(df)

# ================= CERTIFICATE =================
if menu == "Certificates":
    st.subheader("Certificates")

    sub = load_sub()
    team = st.selectbox("Team", sub["Team Name"])

    if st.button("Generate"):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()

        story = []
        story.append(Paragraph("Certificate of Achievement", styles["Title"]))
        story.append(Paragraph(f"This certifies that <b>{team}</b>", styles["Normal"]))
        story.append(Paragraph("has successfully participated in the Hackathon.", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)

        st.download_button("Download", buffer, f"{team}_certificate.pdf")

# ================= REPORT =================
if menu == "Reports":
    st.subheader("Reports")

    ev = load_eval()
    st.download_button("Download CSV", ev.to_csv(index=False), "report.csv")
