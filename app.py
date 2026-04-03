import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="CSE Hackathon Platform", layout="wide")

# ---------------------------
# HEADER
# ---------------------------
st.markdown("""
<div style='text-align:center'>
<h1>🚀 CSE Hackathon Platform</h1>
<p>
Developed by <b>Mr. Mohit Tiwari</b><br>
Assistant Professor, Department of Computer Science and Engineering<br>
Cybersecurity & AI Research<br>
Bharati Vidyapeeth’s College of Engineering, Delhi
</p>
</div>
<hr>
""", unsafe_allow_html=True)

# ---------------------------
# ADMIN SETTINGS
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

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1lLjkJ2IFxZTbKhJV_KCoTZqD1fKrDN5OT5e1qhe7iCE/edit#gid=0"
sheet = client.open_by_url(SHEET_URL).worksheet("Sheet1")

def load_data():
    return pd.DataFrame(sheet.get_all_records())

def add_data(row):
    sheet.append_row(row)

def update_scores(row_index, scores, evaluator_name):
    idea_score, innovation, feasibility, impact = scores
    total = sum(scores)
    eval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.update_cell(row_index, 5, idea_score)
    sheet.update_cell(row_index, 6, innovation)
    sheet.update_cell(row_index, 7, feasibility)
    sheet.update_cell(row_index, 8, impact)
    sheet.update_cell(row_index, 9, total)
    sheet.update_cell(row_index, 10, evaluator_name)
    sheet.update_cell(row_index, 11, eval_time)

# ---------------------------
# LOGIN
# ---------------------------
def show_login():
    st.subheader("🔐 Admin Login")

    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        name = st.text_input("Evaluator Name")
        btn = st.form_submit_button("Login")

        if btn:
            if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
                if name.strip() == "":
                    st.error("Enter Evaluator Name")
                else:
                    st.session_state.is_admin = True
                    st.session_state.evaluator_name = name.strip()
                    st.success("Login successful")
                    st.rerun()
            else:
                st.error("Invalid credentials")

# ---------------------------
# SIDEBAR
# ---------------------------
if st.session_state.is_admin:
    menu = st.sidebar.radio("Menu", [
        "Home", "Submit", "Bulk Upload", "View", "Evaluate", "Leaderboard", "Report", "Login"
    ])
else:
    menu = st.sidebar.radio("Menu", [
        "Home", "Submit", "View", "Leaderboard", "Login"
    ])

if st.session_state.is_admin:
    st.sidebar.success(f"Logged in: {st.session_state.evaluator_name}")
    if st.sidebar.button("Logout"):
        st.session_state.is_admin = False
        st.session_state.evaluator_name = ""
        st.rerun()

# ---------------------------
# HOME
# ---------------------------
if menu == "Home":
    df = load_data()
    total = len(df)
    evaluated = df["Total"].astype(str).replace("", pd.NA).dropna().shape[0] if not df.empty else 0
    pending = total - evaluated

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Ideas", total)
    c2.metric("Evaluated", evaluated)
    c3.metric("Pending", pending)

# ---------------------------
# SUBMIT
# ---------------------------
elif menu == "Submit":
    with st.form("submit"):
        t = st.text_input("Team Name")
        m = st.text_area("Members")
        d = st.selectbox("Domain", ["AI","Cyber","Web","Cloud","Other"])
        i = st.text_area("Idea")
        s = st.form_submit_button("Submit")

        if s:
            if t and i:
                add_data([t,m,d,i,"","","","","","",""])
                st.success("Submitted")
            else:
                st.warning("Fill required fields")

# ---------------------------
# BULK UPLOAD
# ---------------------------
elif menu == "Bulk Upload":
    if not st.session_state.is_admin:
        st.error("Admin only")
    else:
        file = st.file_uploader("Upload CSV", type=["csv"])

        if file:
            df = pd.read_csv(file)
            for _, r in df.iterrows():
                add_data([
                    r["Team Name"], r["Members"], r["Domain"], r["Idea"],
                    "", "", "", "", "", "", ""
                ])
            st.success("Uploaded")

# ---------------------------
# VIEW
# ---------------------------
elif menu == "View":
    df = load_data()
    st.dataframe(df)

# ---------------------------
# EVALUATE
# ---------------------------
elif menu == "Evaluate":
    if not st.session_state.is_admin:
        st.error("Admin only")
    else:
        df = load_data()

        if df.empty:
            st.warning("No data")
        else:
            team = st.selectbox("Team", df["Team Name"])
            idx = df[df["Team Name"] == team].index[0]

            # 🔒 LOCK IF ALREADY EVALUATED
            if str(df.loc[idx, "Total"]).strip() != "":
                st.warning("Already evaluated. Editing locked.")
                st.stop()

            st.write("Evaluator:", st.session_state.evaluator_name)

            a = st.slider("Idea Score",0,10)
            b = st.slider("Innovation",0,10)
            c = st.slider("Feasibility",0,10)
            d = st.slider("Impact",0,10)

            if st.button("Save"):
                update_scores(idx+2,[a,b,c,d],st.session_state.evaluator_name)
                st.success("Saved")

# ---------------------------
# LEADERBOARD
# ---------------------------
elif menu == "Leaderboard":
    df = load_data()
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce")
    df = df.sort_values("Total", ascending=False)
    st.dataframe(df)

# ---------------------------
# REPORT
# ---------------------------
elif menu == "Report":
    if not st.session_state.is_admin:
        st.error("Admin only")
    else:
        df = load_data()
        st.download_button("Download CSV", df.to_csv(index=False), "report.csv")

# ---------------------------
# LOGIN
# ---------------------------
elif menu == "Login":
    if st.session_state.is_admin:
        st.success("Already logged in")
    else:
        show_login()
