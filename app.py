import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="CSE Hackathon Platform", layout="wide")

st.title("🚀 CSE Hackathon Platform – BVCOE Delhi")
st.markdown("### 🔥 Hack@BVP 7.0 – Official Platform")
st.caption("Developed by: Mr. Mohit Tiwari, Assistant Professor, CSE, BVCOE Delhi")

menu = st.sidebar.selectbox("Navigation", ["Home", "Submit Idea", "View Submissions"])

file = "data.csv"

# Initialize file
if not os.path.exists(file):
    df = pd.DataFrame(columns=["Team Name", "Members", "Domain", "Idea"])
    df.to_csv(file, index=False)

# HOME
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

# SUBMIT
elif menu == "Submit Idea":
    st.markdown("## 📩 Submit Your Idea")

    with st.form("form"):
        team = st.text_input("Team Name")
        members = st.text_input("Team Members")
        domain = st.selectbox("Domain", ["AI", "Cybersecurity", "Cloud", "Web", "Blockchain"])
        idea = st.text_area("Describe Your Idea")

        submit = st.form_submit_button("Submit")

        if submit:
            new_data = pd.DataFrame([[team, members, domain, idea]],
                                    columns=["Team Name", "Members", "Domain", "Idea"])
            new_data.to_csv(file, mode='a', header=False, index=False)
            st.success("✅ Submission Recorded Successfully!")

# VIEW
elif menu == "View Submissions":
    st.markdown("## 📊 Live Submissions")

    if os.path.exists(file):
        df = pd.read_csv(file)
        st.dataframe(df)
    else:
        st.warning("No submissions yet.")
