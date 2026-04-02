import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="CSE Hackathon Platform", layout="wide")

# ---------------------------
# GOOGLE SHEETS CONNECTION
# ---------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

# 🔥 FINAL FIX: USE FULL URL (MOST RELIABLE)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lLjkJ2IFxZTbKhJV_KCoTZqD1fKrDN5OT5e1qhe7iCE/edit#gid=0"

sheet = client.open_by_url(SHEET_URL).worksheet("Sheet1")

# ---------------------------
# FUNCTIONS
# ---------------------------
def load_data():
    try:
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Load Error: {e}")
        return pd.DataFrame()

def add_data(row):
    try:
        sheet.append_row(row)
        st.success("✅ Data written to Google Sheet")
    except Exception as e:
        st.error(f"Write Error: {e}")

def update_scores(row_index, scores):
    try:
        for i, score in enumerate(scores):
            sheet.update_cell(row_index, 5 + i, score)

        total = sum(scores)
        sheet.update_cell(row_index, 8, total)

        st.success("✅ Scores saved successfully")
    except Exception as e:
        st.error(f"Update Error: {e}")

# ---------------------------
# SIDEBAR
# ---------------------------
menu = st.sidebar.radio(
    "Navigation",
    ["Home", "Submit Idea", "View Submissions", "Evaluate"]
)

# ---------------------------
# HOME
# ---------------------------
if menu == "Home":
    st.title("🚀 CSE Hackathon Platform")
    st.write("Submit ideas, evaluate them, and rank teams.")

# ---------------------------
# SUBMIT IDEA
# ---------------------------
elif menu == "Submit Idea":
    st.title("📌 Submit Your Idea")

    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if st.session_state.submitted:
        st.success("✅ Idea submitted successfully!")

        if st.button("Submit Another"):
            st.session_state.submitted = False
            st.rerun()

    else:
        with st.form("idea_form", clear_on_submit=True):
            team = st.text_input("Team Name")
            members = st.text_area("Members")
            domain = st.selectbox("Domain", ["AI", "Cybersecurity", "Web", "Cloud", "Other"])
            idea = st.text_area("Idea Description")

            submitted = st.form_submit_button("Submit")

            if submitted:
                if team.strip() == "":
                    st.warning("⚠ Team name required")
                else:
                    add_data([team, members, domain, idea, 0, 0, 0, 0])
                    st.session_state.submitted = True
                    st.rerun()

# ---------------------------
# VIEW SUBMISSIONS
# ---------------------------
elif menu == "View Submissions":
    st.title("📊 All Submissions")

    df = load_data()

    if df.empty:
        st.warning("No data found")
    else:
        st.dataframe(df, use_container_width=True)

# ---------------------------
# EVALUATE
# ---------------------------
elif menu == "Evaluate":
    st.title("🧑‍⚖️ Evaluate Ideas")

    df = load_data()

    if df.empty:
        st.warning("No submissions yet.")
    else:
        team = st.selectbox("Select Team", df["Team Name"])

        idx = df[df["Team Name"] == team].index[0]

        st.write("### Score (0–10)")

        idea_score = st.slider("Idea", 0, 10)
        innovation = st.slider("Innovation", 0, 10)
        feasibility = st.slider("Feasibility", 0, 10)
        impact = st.slider("Impact", 0, 10)

        if st.button("Save Evaluation"):
            update_scores(idx + 2, [idea_score, innovation, feasibility, impact])
            st.rerun()
