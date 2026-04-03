import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="CSE Hackathon Platform", layout="wide")

st.markdown("""
<h1 style='text-align:center'>BVCOE DELHI CSE DEPT. Hackathon Platform</h1>
<p style='text-align:center'>
Developed by <b>Mr. Mohit Tiwari</b><br>
Assistant Professor, Department of Computer Science and Engineering<br>
Cybersecurity & AI Research<br>
Bharati Vidyapeeth’s College of Engineering, Delhi
</p><hr>
""", unsafe_allow_html=True)

# ---------------------------
# ADMIN
# ---------------------------
ADMIN_USERNAME = st.secrets.get("admin_username", "admin")
ADMIN_PASSWORD = st.secrets.get("admin_password", "admin123")

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "evaluator_name" not in st.session_state:
    st.session_state.evaluator_name = ""

# ---------------------------
# GOOGLE SHEETS
# ---------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1lLjkJ2IFxZTbKhJV_KCoTZqD1fKrDN5OT5e1qhe7iCE/edit"
wb = client.open_by_url(SHEET_URL)

sub_sheet = wb.worksheet("Submissions")
eval_sheet = wb.worksheet("Evaluations")

# ---------------------------
# WEIGHTAGE SYSTEM
# ---------------------------
WEIGHTS = {
    "Idea Score": 0.25,
    "Innovation": 0.25,
    "Feasibility": 0.25,
    "Impact": 0.25
}

# ---------------------------
# FUNCTIONS
# ---------------------------
def load_sub():
    return pd.DataFrame(sub_sheet.get_all_records())

def load_eval():
    return pd.DataFrame(eval_sheet.get_all_records())

def add_sub(row):
    sub_sheet.append_row(row)

def already_scored(team, evaluator):
    df = load_eval()
    if df.empty:
        return False
    return ((df["Team Name"] == team) & (df["Evaluator"].str.lower() == evaluator.lower())).any()

def weighted_score(a,b,c,d):
    return round(
        a*WEIGHTS["Idea Score"] +
        b*WEIGHTS["Innovation"] +
        c*WEIGHTS["Feasibility"] +
        d*WEIGHTS["Impact"], 2)

def add_eval(team, evaluator, a,b,c,d):
    total = weighted_score(a,b,c,d)
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    eval_sheet.append_row([team, evaluator, a,b,c,d,total,t])

def leaderboard():
    sub = load_sub()
    ev = load_eval()
    if ev.empty:
        return sub

    for col in ["Idea Score","Innovation","Feasibility","Impact","Weighted Total"]:
        ev[col] = pd.to_numeric(ev[col], errors="coerce")

    agg = ev.groupby("Team Name").agg({
        "Weighted Total":"mean"
    }).reset_index()

    agg.rename(columns={"Weighted Total":"Avg Score"}, inplace=True)
    res = sub.merge(agg, on="Team Name", how="left")
    res = res.sort_values(by="Avg Score", ascending=False)
    return res

def generate_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    data = [df.columns.tolist()] + df.fillna("").values.tolist()

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black)
    ]))

    doc.build([table])
    buffer.seek(0)
    return buffer

# ---------------------------
# LOGIN
# ---------------------------
def login():
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        name = st.text_input("Evaluator Name")
        b = st.form_submit_button("Login")

        if b:
            if u==ADMIN_USERNAME and p==ADMIN_PASSWORD:
                if name.strip()=="":
                    st.error("Enter evaluator name")
                else:
                    st.session_state.is_admin=True
                    st.session_state.evaluator_name=name
                    st.rerun()
            else:
                st.error("Invalid login")

# ---------------------------
# SIDEBAR
# ---------------------------
if st.session_state.is_admin:
    menu = st.sidebar.radio("Menu",
    ["Home","Submit","Evaluate","Leaderboard","Evaluation Log","PDF Report","Login"])
else:
    menu = st.sidebar.radio("Menu",
    ["Home","Submit","Leaderboard","Login"])

if st.session_state.is_admin:
    st.sidebar.success(f"{st.session_state.evaluator_name}")
    if st.sidebar.button("Logout"):
        st.session_state.is_admin=False
        st.session_state.evaluator_name=""
        st.rerun()

# ---------------------------
# HOME
# ---------------------------
if menu=="Home":
    st.subheader("Dashboard")
    st.write("Judge Panel Enabled")

# ---------------------------
# SUBMIT
# ---------------------------
elif menu=="Submit":
    with st.form("sub"):
        t=st.text_input("Team")
        m=st.text_area("Members")
        d=st.selectbox("Domain",["AI","Cyber","Web","Cloud"])
        i=st.text_area("Idea")
        s=st.form_submit_button("Submit")
        if s:
            add_sub([t,m,d,i])
            st.success("Submitted")

# ---------------------------
# EVALUATE
# ---------------------------
elif menu=="Evaluate":
    if not st.session_state.is_admin:
        st.error("Admin only")
    else:
        df=load_sub()
        team=st.selectbox("Team", df["Team Name"])

        if already_scored(team, st.session_state.evaluator_name):
            st.warning("Already evaluated by you")
            st.stop()

        a=st.slider("Idea",0,10)
        b=st.slider("Innovation",0,10)
        c=st.slider("Feasibility",0,10)
        d=st.slider("Impact",0,10)

        if st.button("Submit Score"):
            add_eval(team, st.session_state.evaluator_name,a,b,c,d)
            st.success("Saved")

# ---------------------------
# LEADERBOARD
# ---------------------------
elif menu=="Leaderboard":
    df=leaderboard()
    st.dataframe(df)

# ---------------------------
# LOG
# ---------------------------
elif menu=="Evaluation Log":
    if not st.session_state.is_admin:
        st.error("Admin only")
    else:
        st.dataframe(load_eval())

# ---------------------------
# PDF REPORT
# ---------------------------
elif menu=="PDF Report":
    if not st.session_state.is_admin:
        st.error("Admin only")
    else:
        df=leaderboard()
        pdf=generate_pdf(df)

        st.download_button(
            "Download PDF Report",
            pdf,
            "hackathon_report.pdf",
            "application/pdf"
        )

# ---------------------------
# LOGIN
# ---------------------------
elif menu=="Login":
    if st.session_state.is_admin:
        st.success("Already logged in")
    else:
        login()
