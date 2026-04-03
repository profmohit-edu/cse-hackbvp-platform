import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
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

# ================= GOOGLE SHEETS =================
@st.cache_resource
def connect():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open_by_url(SHEET_URL)
    return wb

wb = connect()
sub_sheet = wb.worksheet("Submissions")
eval_sheet = wb.worksheet("Evaluations")

def load_sub():
    return pd.DataFrame(sub_sheet.get_all_records())

def load_eval():
    return pd.DataFrame(eval_sheet.get_all_records())

# ================= HEADER =================
st.markdown("""
<h1 style='text-align:center;'>🚀 CSE Hackathon Platform</h1>
<p style='text-align:center;'>
Developed by <b>Mr. Mohit Tiwari</b><br>
Assistant Professor, Department of Computer Science and Engineering<br>
Cybersecurity & AI Research<br>
Bharati Vidyapeeth’s College of Engineering, Delhi
</p>
<hr>
""", unsafe_allow_html=True)

# ================= LOGIN =================
st.sidebar.title("Login")

role = st.sidebar.selectbox("Role", ["Guest", "Admin", "Judge"])

if role == "Admin":
    user = st.sidebar.text_input("Username")
    pwd = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            st.session_state.role = "Admin"
            st.success("Admin logged in")

elif role == "Judge":
    name = st.sidebar.text_input("Judge Name")

    if st.sidebar.button("Login"):
        if name != "":
            st.session_state.role = "Judge"
            st.session_state.judge_name = name
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

# ================= SUBMIT =================
if menu == "Submit":
    st.subheader("Submit Idea")

    t = st.text_input("Team")
    m = st.text_area("Members")
    d = st.text_input("Domain")
    i = st.text_area("Idea")

    if st.button("Submit"):
        sub_sheet.append_row([t,m,d,i])
        st.success("Submitted")

# ================= BULK UPLOAD =================
if menu == "Bulk Upload":
    st.subheader("Bulk Upload")

    df_template = pd.DataFrame(columns=["Team Name","Members","Domain","Idea"])
    buffer = BytesIO()
    df_template.to_excel(buffer,index=False)
    buffer.seek(0)

    st.download_button("Download Template", buffer, "template.xlsx")

    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:
        df = pd.read_excel(file)
        st.dataframe(df)

        if st.button("Upload"):
            for _, r in df.iterrows():
                sub_sheet.append_row([r[0],r[1],r[2],r[3]])
            st.success("Uploaded")

# ================= EVALUATE PANEL =================
if menu == "Evaluate Panel":
    st.subheader("Judge Panel")

    df = load_sub()
    ev = load_eval()

    team = st.selectbox("Select Team", df["Team Name"])

    # LOCK
    if not ev.empty:
        if ((ev["Team Name"] == team) &
            (ev["Judge"] == st.session_state.judge_name)).any():
            st.warning("Already evaluated by you")
            st.stop()

    c1,c2,c3 = st.columns(3)

    with c1:
        idea = st.slider("Idea",0,10,5)
        innovation = st.slider("Innovation",0,10,5)

    with c2:
        tech = st.slider("Technical",0,10,5)
        pres = st.slider("Presentation",0,10,5)

    with c3:
        impact = st.slider("Impact",0,10,5)

    total = round(
        idea*WEIGHTS["Idea"] +
        innovation*WEIGHTS["Innovation"] +
        tech*WEIGHTS["Technical"] +
        pres*WEIGHTS["Presentation"] +
        impact*WEIGHTS["Impact"],2
    )

    st.info(f"Score: {total}")

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
    st.subheader("Leaderboard")

    sub = load_sub()
    ev = load_eval()

    if not ev.empty:
        ev["Total"] = pd.to_numeric(ev["Total"], errors='coerce')
        agg = ev.groupby("Team Name")["Total"].mean().reset_index()

        df = sub.merge(agg,on="Team Name",how="left")
        df = df.sort_values(by="Total",ascending=False)

        st.dataframe(df)

# ================= CERTIFICATES =================
if menu == "Certificates":
    st.subheader("Generate Certificates")

    sub = load_sub()

    team = st.selectbox("Team", sub["Team Name"])

    if st.button("Generate Certificate"):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()

        story = []
        story.append(Paragraph("Certificate of Achievement", styles["Title"]))
        story.append(Paragraph(f"This is to certify that {team}", styles["Normal"]))
        story.append(Paragraph("has successfully participated in Hackathon", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)

        st.download_button("Download Certificate", buffer, f"{team}_certificate.pdf")

# ================= REPORT =================
if menu == "Reports":
    st.subheader("Reports")

    ev = load_eval()

    st.download_button("CSV", ev.to_csv(index=False), "report.csv")
