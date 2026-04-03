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
# GOOGLE SHEETS CONNECTION
# ---------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1lLjkJ2IFxZTbKhJV_KCoTZqD1fKrDN5OT5e1qhe7iCE/edit#gid=0"
workbook = client.open_by_url(SHEET_URL)

submissions_sheet = workbook.worksheet("Sheet1")
evaluations_sheet = workbook.worksheet("Evaluations")

# ---------------------------
# FUNCTIONS
# ---------------------------
def load_submissions():
    try:
        return pd.DataFrame(submissions_sheet.get_all_records())
    except:
        return pd.DataFrame(columns=["Team Name", "Members", "Domain", "Idea"])

def load_evaluations():
    try:
        return pd.DataFrame(evaluations_sheet.get_all_records())
    except:
        return pd.DataFrame(columns=[
            "Team Name", "Evaluator", "Idea Score", "Innovation",
            "Feasibility", "Impact", "Total", "Evaluation Time"
        ])

def add_submission(row):
    submissions_sheet.append_row(row)

def add_evaluation(team_name, evaluator, idea_score, innovation, feasibility, impact):
    total = idea_score + innovation + feasibility + impact
    eval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    evaluations_sheet.append_row([
        team_name, evaluator, idea_score, innovation, feasibility, impact, total, eval_time
    ])

def has_evaluator_already_scored(team_name, evaluator_name):
    eval_df = load_evaluations()
    if eval_df.empty:
        return False
    filtered = eval_df[
        (eval_df["Team Name"].astype(str).str.strip() == str(team_name).strip()) &
        (eval_df["Evaluator"].astype(str).str.strip().str.lower() == str(evaluator_name).strip().lower())
    ]
    return len(filtered) > 0

def build_leaderboard():
    sub_df = load_submissions()
    eval_df = load_evaluations()

    if sub_df.empty:
        return pd.DataFrame()

    if eval_df.empty:
        result = sub_df.copy()
        result["Avg Idea Score"] = ""
        result["Avg Innovation"] = ""
        result["Avg Feasibility"] = ""
        result["Avg Impact"] = ""
        result["Avg Total"] = ""
        result["No. of Evaluations"] = 0
        return result

    for col in ["Idea Score", "Innovation", "Feasibility", "Impact", "Total"]:
        eval_df[col] = pd.to_numeric(eval_df[col], errors="coerce")

    agg_df = eval_df.groupby("Team Name", dropna=False).agg(
        **{
            "Avg Idea Score": ("Idea Score", "mean"),
            "Avg Innovation": ("Innovation", "mean"),
            "Avg Feasibility": ("Feasibility", "mean"),
            "Avg Impact": ("Impact", "mean"),
            "Avg Total": ("Total", "mean"),
            "No. of Evaluations": ("Total", "count")
        }
    ).reset_index()

    result = sub_df.merge(agg_df, on="Team Name", how="left")

    for col in ["Avg Idea Score", "Avg Innovation", "Avg Feasibility", "Avg Impact", "Avg Total"]:
        result[col] = result[col].round(2)

    result["No. of Evaluations"] = result["No. of Evaluations"].fillna(0).astype(int)
    result = result.sort_values(by=["Avg Total", "No. of Evaluations"], ascending=[False, False], na_position="last")

    return result

def show_login():
    st.subheader("🔐 Admin Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        evaluator_name = st.text_input("Evaluator Name")
        btn = st.form_submit_button("Login")

        if btn:
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                if evaluator_name.strip() == "":
                    st.error("Enter Evaluator Name")
                else:
                    st.session_state.is_admin = True
                    st.session_state.evaluator_name = evaluator_name.strip()
                    st.success("Login successful")
                    st.rerun()
            else:
                st.error("Invalid credentials")

# ---------------------------
# SIDEBAR
# ---------------------------
if st.session_state.is_admin:
    menu = st.sidebar.radio("Menu", [
        "Home", "Submit", "Bulk Upload", "View", "Evaluate", "Leaderboard", "Evaluation Log", "Report", "Login"
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
    submissions_df = load_submissions()
    eval_df = load_evaluations()
    leaderboard_df = build_leaderboard()

    total_ideas = len(submissions_df)
    total_evaluations = len(eval_df)
    evaluated_teams = 0 if leaderboard_df.empty else int((leaderboard_df["No. of Evaluations"] > 0).sum())
    pending_teams = total_ideas - evaluated_teams

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Ideas", total_ideas)
    c2.metric("Evaluated Teams", evaluated_teams)
    c3.metric("Pending Teams", pending_teams)
    c4.metric("Total Evaluations Logged", total_evaluations)

# ---------------------------
# SUBMIT
# ---------------------------
elif menu == "Submit":
    st.subheader("📌 Submit Idea")

    with st.form("submit_form", clear_on_submit=True):
        team = st.text_input("Team Name")
        members = st.text_area("Members")
        domain = st.selectbox("Domain", ["AI", "Cybersecurity", "Web", "Cloud", "Other"])
        idea = st.text_area("Idea")
        btn = st.form_submit_button("Submit")

        if btn:
            if team.strip() == "" or idea.strip() == "":
                st.warning("Team Name and Idea are required.")
            else:
                existing_df = load_submissions()
                if not existing_df.empty and existing_df["Team Name"].astype(str).str.strip().str.lower().eq(team.strip().lower()).any():
                    st.error("A team with this name already exists. Use a unique Team Name.")
                else:
                    add_submission([team, members, domain, idea])
                    st.success("Idea submitted successfully.")

# ---------------------------
# BULK UPLOAD
# ---------------------------
elif menu == "Bulk Upload":
    if not st.session_state.is_admin:
        st.error("Admin only")
    else:
        st.subheader("📥 Bulk Upload Ideas")

        template_df = pd.DataFrame({
            "Team Name": [],
            "Members": [],
            "Domain": [],
            "Idea": []
        })

        st.download_button(
            label="⬇ Download CSV Template",
            data=template_df.to_csv(index=False),
            file_name="hackathon_submission_template.csv",
            mime="text/csv"
        )

        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df, use_container_width=True)

            if st.button("Upload File Data"):
                existing_df = load_submissions()
                existing_names = set()
                if not existing_df.empty:
                    existing_names = set(existing_df["Team Name"].astype(str).str.strip().str.lower().tolist())

                count = 0
                skipped = 0

                for _, row in df.iterrows():
                    team_name = str(row.get("Team Name", "")).strip()
                    if team_name == "":
                        skipped += 1
                        continue

                    if team_name.lower() in existing_names:
                        skipped += 1
                        continue

                    add_submission([
                        team_name,
                        row.get("Members", ""),
                        row.get("Domain", ""),
                        row.get("Idea", "")
                    ])
                    existing_names.add(team_name.lower())
                    count += 1

                st.success(f"{count} record(s) uploaded successfully.")
                if skipped > 0:
                    st.warning(f"{skipped} record(s) skipped due to blank/duplicate Team Name.")

# ---------------------------
# VIEW
# ---------------------------
elif menu == "View":
    st.subheader("📋 Submitted Ideas")
    df = load_submissions()
    if df.empty:
        st.info("No submissions found.")
    else:
        st.dataframe(df, use_container_width=True)

# ---------------------------
# EVALUATE
# ---------------------------
elif menu == "Evaluate":
    if not st.session_state.is_admin:
        st.error("Admin only")
    else:
        st.subheader("🧑‍⚖️ Evaluate Team")

        submissions_df = load_submissions()

        if submissions_df.empty:
            st.info("No teams available for evaluation.")
        else:
            team = st.selectbox("Select Team", submissions_df["Team Name"].astype(str).tolist())

            if has_evaluator_already_scored(team, st.session_state.evaluator_name):
                st.warning("You have already evaluated this team. Re-evaluation is locked for the same evaluator.")
                st.stop()

            st.markdown(f"**Evaluator:** {st.session_state.evaluator_name}")

            idea_score = st.slider("Idea Score", 0, 10)
            innovation = st.slider("Innovation", 0, 10)
            feasibility = st.slider("Feasibility", 0, 10)
            impact = st.slider("Impact", 0, 10)

            if st.button("Save Evaluation"):
                add_evaluation(
                    team,
                    st.session_state.evaluator_name,
                    idea_score,
                    innovation,
                    feasibility,
                    impact
                )
                st.success("Evaluation saved successfully.")
                st.rerun()

# ---------------------------
# LEADERBOARD
# ---------------------------
elif menu == "Leaderboard":
    st.subheader("🏆 Leaderboard")

    leaderboard_df = build_leaderboard()

    if leaderboard_df.empty:
        st.info("No data available.")
    else:
        st.dataframe(leaderboard_df, use_container_width=True)

        st.markdown("### Top 3 Teams")
        ranked_df = leaderboard_df.dropna(subset=["Avg Total"]).head(3)

        if ranked_df.empty:
            st.info("No evaluated teams yet.")
        else:
            medals = ["🥇", "🥈", "🥉"]
            for i, (_, row) in enumerate(ranked_df.iterrows()):
                st.write(f"{medals[i]} {row['Team Name']} — Average Score: {row['Avg Total']} ({row['No. of Evaluations']} evaluation(s))")

# ---------------------------
# EVALUATION LOG
# ---------------------------
elif menu == "Evaluation Log":
    if not st.session_state.is_admin:
        st.error("Admin only")
    else:
        st.subheader("🧾 Evaluation Log")
        eval_df = load_evaluations()
        if eval_df.empty:
            st.info("No evaluations logged yet.")
        else:
            st.dataframe(eval_df, use_container_width=True)

# ---------------------------
# REPORT
# ---------------------------
elif menu == "Report":
    if not st.session_state.is_admin:
        st.error("Admin only")
    else:
        st.subheader("📄 Export Reports")

        leaderboard_df = build_leaderboard()
        eval_df = load_evaluations()

        if not leaderboard_df.empty:
            st.download_button(
                "Download Leaderboard CSV",
                leaderboard_df.to_csv(index=False),
                "leaderboard_report.csv",
                "text/csv"
            )

        if not eval_df.empty:
            st.download_button(
                "Download Evaluation Log CSV",
                eval_df.to_csv(index=False),
                "evaluation_log_report.csv",
                "text/csv"
            )

# ---------------------------
# LOGIN
# ---------------------------
elif menu == "Login":
    if st.session_state.is_admin:
        st.success(f"Already logged in as {st.session_state.evaluator_name}")
    else:
        show_login()
