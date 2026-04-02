import streamlit as st
import pandas as pd
import os

# -------------------- CONFIG --------------------
st.set_page_config(page_title="CSE Hackathon Platform", layout="wide")

# -------------------- HEADER --------------------
st.title("🚀 CSE Hackathon Platform – BVCOE Delhi")
st.markdown("### 🔥 Hack@BVP 7.0 – Official Platform")
st.caption("Developed by: Mr. Mohit Tiwari, Assistant Professor, CSE, BVCOE Delhi")

# -------------------- SIDEBAR --------------------
menu = st.sidebar.selectbox("Navigation", ["Home", "Submit Idea", "View Submissions", "Evaluate"])

# -------------------- FILE SETUP --------------------
file = "data.csv"

columns = ["Team Name", "Members", "Domain", "Idea", "Innovation", "Feasibility", "Impact", "Total"]

if not os.path.exists(file):
    df = pd.DataFrame(columns=columns)
    df.to_csv(file, index=False)

# -------------------- HOME --------------------
if menu == "Home":
    st.markdown("## 🎯 Hackathon Domains")
    st.info("AI | Cybersecurity | Cloud | Web | Blockchain")

    st.markdown("## 💡 Why Participate?")
    st.write("""
    - Build real-world solutions  
    - Convert into Final Year Project  
    - Publish research paper  
    - Explore startup potential  
    """)

    st.markdown("## 🧠 Outcome Path")
    st.success("Hackathon → Project → Paper → Startup")

# -------------------- SUBMIT --------------------
elif menu == "Submit Idea":
    st.markdown("## 📩 Submit Your Idea")

    with st.form("form", clear_on_submit=True):
        team = st.text_input("Team Name")
        members = st.text_input("Team Members")
        domain = st.selectbox("Domain", ["AI", "Cybersecurity", "Cloud", "Web", "Blockchain"])
        idea = st.text_area("Describe Your Idea")

        submit = st.form_submit_button("Submit")

        if submit:
            if team and members and idea:
                new_data = pd.DataFrame([[team, members, domain, idea, 0, 0, 0, 0]],
                                        columns=columns)
                new_data.to_csv(file, mode='a', header=False, index=False)

                st.success("✅ Submission Recorded Successfully!")
                st.rerun()
            else:
                st.warning("⚠️ Fill all fields")

# -------------------- VIEW --------------------
elif menu == "View Submissions":
    st.markdown("## 📊 Submissions & Rankings")

    df = pd.read_csv(file)

    if len(df) > 0:
        df_sorted = df.sort_values(by="Total", ascending=False)
        st.dataframe(df_sorted, use_container_width=True)
    else:
        st.info("No submissions yet")

# -------------------- EVALUATION --------------------
elif menu == "Evaluate":
    st.markdown("## 🧮 Evaluate Projects")

    df = pd.read_csv(file)

    if len(df) > 0:
        team_list = df["Team Name"].tolist()
        selected_team = st.selectbox("Select Team", team_list)

        index = df[df["Team Name"] == selected_team].index[0]

        innovation = st.slider("Innovation (0-10)", 0, 10, int(df.at[index, "Innovation"]))
        feasibility = st.slider("Feasibility (0-10)", 0, 10, int(df.at[index, "Feasibility"]))
        impact = st.slider("Impact (0-10)", 0, 10, int(df.at[index, "Impact"]))

        total = innovation + feasibility + impact

        if st.button("Save Evaluation"):
            df.at[index, "Innovation"] = innovation
            df.at[index, "Feasibility"] = feasibility
            df.at[index, "Impact"] = impact
            df.at[index, "Total"] = total

            df.to_csv(file, index=False)

            st.success(f"✅ Score Saved! Total = {total}")
            st.rerun()
    else:
        st.warning("No teams available to evaluate")
