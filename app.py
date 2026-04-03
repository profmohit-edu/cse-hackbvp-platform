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
    font-size: 36px;
    font-weight: 700;
}
.subtitle {
    text-align: center;
    font-size: 16px;
    color: gray;
}
.card {
    padding: 20px;
    border-radius: 12px;
    background: white;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
    text-align: center;
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
Assistant Professor | Cybersecurity & AI<br>
BVCOE Delhi
</div>
<hr>
""", unsafe_allow_html=True)

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
        return pd.DataFrame(sheet.get_all_records())
    except:
        return pd.DataFrame()

def add_data(row):
    sheet.append_row(row)

def update_scores(row_index, scores):
    for i, score in enumerate(scores):
        sheet.update_cell(row_index, 5 + i, score)
    sheet.update_cell(row_index, 9, sum(scores))

# ---------------------------
# SIDEBAR
# ---------------------------
menu = st.sidebar.radio(
    "Navigation",
    ["Home", "Submit Idea", "Bulk Upload", "View Submissions", "Evaluate", "Leaderboard"]
)

# ---------------------------
# HOME
# ---------------------------
if menu == "Home":
    st.markdown("## Dashboard Overview")

    df = load_data()

    total = len(df)
    evaluated = df[df["Total"] != ""].shape[0] if not df.empty else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"<div class='card'><h3>{total}</h3><p>Total Ideas</p></div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"<div class='card'><h3>{evaluated}</h3><p>Evaluated</p></div>", unsafe_allow_html=True)

    with col3:
        st.markdown(f"<div class='card'><h3>{total - evaluated}</h3><p>Pending</p></div>", unsafe_allow_html=True)

# ---------------------------
# SUBMIT IDEA
# ---------------------------
elif menu == "Submit Idea":
    st.title("Submit Idea")

    with st.form("form", clear_on_submit=True):
        team = st.text_input("Team Name")
        members = st.text_area("Members")
        domain = st.selectbox("Domain", ["AI", "Cybersecurity", "Web", "Cloud", "Other"])
        idea = st.text_area("Idea Description")

        submit = st.form_submit_button("Submit")

        if submit:
            add_data([team, members, domain, idea, "", "", "", "", ""])
            st.success("Submitted successfully!")

# ---------------------------
# BULK UPLOAD
# ---------------------------
elif menu == "Bulk Upload":
    st.title("📥 Bulk Upload Ideas")

    # TEMPLATE DOWNLOAD
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

            st.write("Preview:")
            st.dataframe(df)

            if st.button("Upload to System"):
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

                st.success("✅ Bulk upload successful!")

        except Exception as e:
            st.error(f"Error: {e}")

# ---------------------------
# VIEW SUBMISSIONS
# ---------------------------
elif menu == "View Submissions":
    st.title("Submissions")

    df = load_data()

    if df.empty:
        st.warning("No data")
    else:
        st.dataframe(df, use_container_width=True)

# ---------------------------
# EVALUATE
# ---------------------------
elif menu == "Evaluate":
    st.title("Evaluate Ideas")

    df = load_data()

    if df.empty:
        st.warning("No data")
    else:
        team = st.selectbox("Select Team", df["Team Name"])
        idx = df[df["Team Name"] == team].index[0]

        idea = st.slider("Idea", 0, 10)
        innovation = st.slider("Innovation", 0, 10)
        feasibility = st.slider("Feasibility", 0, 10)
        impact = st.slider("Impact", 0, 10)

        if st.button("Save"):
            update_scores(idx + 2, [idea, innovation, feasibility, impact])
            st.success("Saved!")

# ---------------------------
# LEADERBOARD
# ---------------------------
elif menu == "Leaderboard":
    st.title("Leaderboard")

    df = load_data()

    if df.empty:
        st.warning("No data")
    else:
        df["Total"] = pd.to_numeric(df["Total"], errors="coerce")
        df = df.sort_values(by="Total", ascending=False)

        st.dataframe(df, use_container_width=True)

        st.subheader("Top 3 Teams")

        for _, row in df.head(3).iterrows():
            st.write(f"🏆 {row['Team Name']} — {row['Total']}")
