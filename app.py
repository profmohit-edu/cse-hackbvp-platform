import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="CSE Hackathon Platform", layout="wide")

# ---------------------------
# CUSTOM CSS
# ---------------------------
st.markdown("""
<style>
.main {
    background-color: #f5f7fa;
}
.title {
    text-align: center;
    font-size: 38px;
    font-weight: 800;
}
.subtitle {
    text-align: center;
    font-size: 16px;
    color: gray;
    line-height: 1.6;
}
.card {
    padding: 25px;
    border-radius: 14px;
    background: white;
    box-shadow: 0px 6px 14px rgba(0,0,0,0.06);
    text-align: center;
}
.card-blue { border-left: 6px solid #007bff; }
.card-green { border-left: 6px solid #28a745; }
.card-orange { border-left: 6px solid #fd7e14; }
.small-note {
    font-size: 14px;
    color: gray;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# HEADER
# ---------------------------
st.markdown("""
<div class='title'>🚀 CSE Hackathon Platform</div>
<div class='subtitle'>
Developed by <b>Mr. Mohit Tiwari</b><br>
Assistant Professor, Department of Computer Science and Engineering<br>
Cybersecurity & AI Research<br>
Bharati Vidyapeeth’s College of Engineering, Delhi
</div>
<hr>
""", unsafe_allow_html=True)

# ---------------------------
# ADMIN LOGIN SETTINGS
# ---------------------------
# IMPORTANT:
# Add these in Streamlit Secrets:
#
# admin_username = "your_username"
# admin_password = "your_password"
#
# Example:
# admin_username = "mohit"
# admin_password = "hackathon123"

ADMIN_USERNAME = st.secrets.get("admin_username", "admin")
ADMIN_PASSWORD = st.secrets.get("admin_password", "admin123")

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

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
sheet = client.open_by_url(SHEET_URL).worksheet("Sheet1")

# ---------------------------
# FUNCTIONS
# ---------------------------
def load_data():
    try:
        df = pd.DataFrame(sheet.get_all_records())
        return df
    except:
        return pd.DataFrame()

def add_data(row):
    sheet.append_row(row)

def update_scores(row_index, scores):
    for i, score in enumerate(scores):
        sheet.update_cell(row_index, 5 + i, score)
    sheet.update_cell(row_index, 9, sum(scores))

def show_login_box():
    st.subheader("🔐 Faculty/Admin Login")
    with st.form("admin_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

        if login_btn:
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.success("✅ Login successful")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

def show_logout_button():
    if st.session_state.is_admin:
        st.sidebar.success("Admin Logged In")
        if st.sidebar.button("Logout"):
            st.session_state.is_admin = False
            st.rerun()

# ---------------------------
# SIDEBAR
# ---------------------------
if st.session_state.is_admin:
    menu_options = ["Home", "Submit Idea", "Bulk Upload", "View Submissions", "Evaluate", "Leaderboard", "Admin Login"]
else:
    menu_options = ["Home", "Submit Idea", "View Submissions", "Leaderboard", "Admin Login"]

menu = st.sidebar.radio("Navigation", menu_options)
show_logout_button()

# ---------------------------
# HOME
# ---------------------------
if menu == "Home":
    st.markdown("## 📊 Dashboard Overview")

    df = load_data()

    total = len(df)
    if not df.empty and "Total" in df.columns:
        temp_total = pd.to_numeric(df["Total"], errors="coerce")
        evaluated = temp_total.notna().sum()
    else:
        evaluated = 0
    pending = total - evaluated

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class='card card-blue'>
            <h2>📌 {total}</h2>
            <p>Total Ideas</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='card card-green'>
            <h2>✅ {evaluated}</h2>
            <p>Evaluated</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='card card-orange'>
            <h2>⏳ {pending}</h2>
            <p>Pending</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.is_admin:
        st.info("Admin access enabled: Bulk Upload and Evaluate sections are visible.")
    else:
        st.info("Student/Public view enabled: submission and leaderboard are available.")

# ---------------------------
# SUBMIT IDEA
# ---------------------------
elif menu == "Submit Idea":
    st.title("Submit Idea")

    with st.form("submit_form", clear_on_submit=True):
        team = st.text_input("Team Name")
        members = st.text_area("Members")
        domain = st.selectbox("Domain", ["AI", "Cybersecurity", "Web", "Cloud", "Other"])
        idea = st.text_area("Idea Description")
        submit = st.form_submit_button("Submit")

        if submit:
            if not team.strip():
                st.warning("Please enter Team Name.")
            elif not idea.strip():
                st.warning("Please enter Idea Description.")
            else:
                add_data([team, members, domain, idea, "", "", "", "", ""])
                st.success("✅ Idea submitted successfully!")

# ---------------------------
# BULK UPLOAD (ADMIN ONLY)
# ---------------------------
elif menu == "Bulk Upload":
    if not st.session_state.is_admin:
        st.error("❌ Access denied. Admin login required.")
    else:
        st.title("📥 Bulk Upload Ideas")

        template_df = pd.DataFrame({
            "Team Name": [],
            "Members": [],
            "Domain": [],
            "Idea": [],
            "Idea Score": [],
            "Innovation": [],
            "Feasibility": [],
            "Impact": [],
            "Total": []
        })

        st.download_button(
            label="⬇ Download Excel Template",
            data=template_df.to_csv(index=False),
            file_name="hackathon_template.csv",
            mime="text/csv"
        )

        st.markdown("---")

        uploaded_file = st.file_uploader("Upload filled file", type=["csv", "xlsx"])

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.subheader("📊 Preview of Uploaded Data")
                st.dataframe(df, use_container_width=True)

                if st.button("🚀 Upload to System"):
                    count = 0

                    for _, row in df.iterrows():
                        sheet.append_row([
                            row["Team Name"],
                            row["Members"],
                            row["Domain"],
                            row["Idea"],
                            row.get("Idea Score", ""),
                            row.get("Innovation", ""),
                            row.get("Feasibility", ""),
                            row.get("Impact", ""),
                            row.get("Total", "")
                        ])
                        count += 1

                    st.success(f"✅ {count} records uploaded successfully!")

                    st.subheader("📌 Latest Data in System")
                    new_df = load_data()
                    st.dataframe(new_df.tail(10), use_container_width=True)

            except Exception as e:
                st.error(f"❌ Error: {e}")

# ---------------------------
# VIEW SUBMISSIONS
# ---------------------------
elif menu == "View Submissions":
    st.title("Submissions")

    df = load_data()

    if df.empty:
        st.warning("No data available.")
    else:
        st.dataframe(df, use_container_width=True)

# ---------------------------
# EVALUATE (ADMIN ONLY)
# ---------------------------
elif menu == "Evaluate":
    if not st.session_state.is_admin:
        st.error("❌ Access denied. Admin login required.")
    else:
        st.title("Evaluate Ideas")

        df = load_data()

        if df.empty:
            st.warning("No data available.")
        else:
            team = st.selectbox("Select Team", df["Team Name"])
            idx = df[df["Team Name"] == team].index[0]

            st.markdown("### Scoring Parameters")
            idea_score = st.slider("Idea Score", 0, 10)
            innovation = st.slider("Innovation", 0, 10)
            feasibility = st.slider("Feasibility", 0, 10)
            impact = st.slider("Impact", 0, 10)

            if st.button("Save Evaluation"):
                update_scores(idx + 2, [idea_score, innovation, feasibility, impact])
                st.success("✅ Evaluation saved successfully!")

# ---------------------------
# LEADERBOARD
# ---------------------------
elif menu == "Leaderboard":
    st.title("Leaderboard")

    df = load_data()

    if df.empty:
        st.warning("No data available.")
    else:
        df["Total"] = pd.to_numeric(df["Total"], errors="coerce")
        df = df.sort_values(by="Total", ascending=False, na_position="last")

        st.dataframe(df, use_container_width=True)

        st.subheader("Top 3 Teams")
        top_df = df.dropna(subset=["Total"]).head(3)

        if top_df.empty:
            st.info("No evaluated teams yet.")
        else:
            medals = ["🥇", "🥈", "🥉"]
            for i, (_, row) in enumerate(top_df.iterrows()):
                st.write(f"{medals[i]} {row['Team Name']} — {int(row['Total'])}")

# ---------------------------
# ADMIN LOGIN
# ---------------------------
elif menu == "Admin Login":
    if st.session_state.is_admin:
        st.success("✅ You are already logged in as Admin.")
        st.markdown("<p class='small-note'>Bulk Upload and Evaluate sections are enabled in the sidebar.</p>", unsafe_allow_html=True)
    else:
        show_login_box()
