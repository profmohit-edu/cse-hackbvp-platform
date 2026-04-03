# =========================================
# 🚀 CSE Hackathon Platform (SQLite-backed)
# Developed by Mr. Mohit Tiwari
# Assistant Professor, CSE Department
# Bharati Vidyapeeth’s College of Engineering, Delhi
# =========================================

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ------------ CONFIG ------------
st.set_page_config(page_title="CSE Hackathon Platform", layout="wide")

DB_PATH = "hackathon.db"

ADMIN_USER = st.secrets.get("admin_user", "admin")
ADMIN_PASS = st.secrets.get("admin_pass", "admin123")

SUBMISSION_HEADERS = ["team_name", "members", "domain", "idea"]
EVALUATION_HEADERS = [
    "team_name", "judge", "idea_score", "innovation",
    "technical", "presentation", "impact", "total", "time"
]

WEIGHTS = {
    "idea_score": 0.20,
    "innovation": 0.30,
    "technical": 0.30,
    "presentation": 0.10,
    "impact": 0.10
}

# ------------ SESSION STATE ------------
if "role" not in st.session_state:
    st.session_state.role = "Guest"
if "judge_name" not in st.session_state:
    st.session_state.judge_name = ""
if "event_end" not in st.session_state:
    st.session_state.event_end = datetime.now() + timedelta(hours=2)
if "prev_top_team" not in st.session_state:
    st.session_state.prev_top_team = None

# ------------ DB HELPERS ------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            team_name TEXT PRIMARY KEY,
            members   TEXT,
            domain    TEXT,
            idea      TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name  TEXT,
            judge      TEXT,
            idea_score INTEGER,
            innovation INTEGER,
            technical  INTEGER,
            presentation INTEGER,
            impact     INTEGER,
            total      REAL,
            time       TEXT
        );
        """
    )
    conn.commit()
    conn.close()

init_db()

def compute_score(idea, innovation, tech, pres, impact):
    return round(
        idea * WEIGHTS["idea_score"]
        + innovation * WEIGHTS["innovation"]
        + tech * WEIGHTS["technical"]
        + pres * WEIGHTS["presentation"]
        + impact * WEIGHTS["impact"],
        2
    )

# ------------ DATA ACCESS LAYER ------------
@st.cache_data(ttl=60)
def load_submissions_df():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM submissions", conn)
    conn.close()
    return df

@st.cache_data(ttl=60)
def load_evaluations_df():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM evaluations", conn)
    conn.close()
    return df

def add_submission(team_name, members, domain, idea):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO submissions (team_name, members, domain, idea)
        VALUES (?, ?, ?, ?)
        """,
        (team_name, members, domain, idea),
    )
    conn.commit()
    conn.close()
    st.cache_data.clear()

def bulk_add_submissions(df: pd.DataFrame):
    conn = get_conn()
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute(
            """
            INSERT OR REPLACE INTO submissions (team_name, members, domain, idea)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(row.get("Team Name", "")).strip(),
                str(row.get("Members", "")),
                str(row.get("Domain", "")),
                str(row.get("Idea", "")),
            ),
        )
    conn.commit()
    conn.close()
    st.cache_data.clear()

def add_evaluation(team_name, judge, idea, innovation, tech, pres, impact, total):
    conn = get_conn()
    cur = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        """
        INSERT INTO evaluations (
            team_name, judge, idea_score, innovation, technical,
            presentation, impact, total, time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (team_name, judge, idea, innovation, tech, pres, impact, total, now_str),
    )
    conn.commit()
    conn.close()
    st.cache_data.clear()

def has_evaluation(team_name, judge):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 1 FROM evaluations
        WHERE team_name = ? AND judge = ?
        LIMIT 1
        """,
        (team_name, judge),
    )
    row = cur.fetchone()
    conn.close()
    return row is not None

def get_leaderboard_df():
    sub = load_submissions_df()
    ev = load_evaluations_df()
    if ev.empty or sub.empty:
        return pd.DataFrame()

    agg = ev.groupby("team_name")["total"].mean().reset_index()
    agg.rename(columns={"total": "final_score"}, inplace=True)
    df = sub.merge(agg, on="team_name", how="left")
    df["final_score"] = df["final_score"].round(2)
    df = df.sort_values(by="final_score", ascending=False, na_position="last")
    return df

# ------------ HEADER UI ------------
st.markdown("""
<div style="
background: linear-gradient(135deg,#f8fafc,#e2e8f0);
padding:20px;border-radius:18px;
box-shadow:0 8px 25px rgba(0,0,0,0.15);
text-align:center;margin-bottom:20px;">
<img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Bvcoe_main.JPG" width="60">
<h2>🚀 CSE Hackathon Platform</h2>
<div style="margin-top:4px;font-size:14px;">
End-to-end platform for CSE hackathon registrations, judging, live leaderboard, and certificates.
</div>
<img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Bvcoe_main.JPG"
style="width:100%;max-height:250px;object-fit:cover;border-radius:14px;margin:10px 10px 0 10px;">
<div style="font-size:20px;font-weight:600;margin-top:10px;">Developed by Mr. Mohit Tiwari</div>
<div>Assistant Professor, CSE Department</div>
<div>Cybersecurity & AI Research</div>
<div>Bharati Vidyapeeth’s College of Engineering, Delhi</div>
<div style="font-size:12px;margin-top:8px;">Image: Wikimedia Commons</div>
</div>
""", unsafe_allow_html=True)

# ------------ LOGIN ------------
with st.expander("🔐 Login"):
    role_choice = st.selectbox("Login As", ["Guest", "Admin", "Judge"])

    if role_choice == "Admin":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login Admin"):
            if u == ADMIN_USER and p == ADMIN_PASS:
                st.session_state.role = "Admin"
                st.success("✅ Admin logged in")
            else:
                st.error("Invalid admin credentials.")

    if role_choice == "Judge":
        name = st.text_input("Judge Name")
        if st.button("Login Judge"):
            if name.strip():
                st.session_state.role = "Judge"
                st.session_state.judge_name = name.strip()
                st.success(f"✅ Judge {name} logged in")
            else:
                st.error("Please enter your name.")

    if role_choice == "Guest":
        st.session_state.role = "Guest"
        st.session_state.judge_name = ""

st.write("Logged in as:", st.session_state.role)

# ------------ MENU ------------
menu = ["Dashboard", "Leaderboard"]
if st.session_state.role == "Admin":
    menu += ["Team Submission", "Bulk Team Import", "Certificates", "Event Control", "Reports & Export"]
if st.session_state.role == "Judge":
    menu += ["Evaluate"]

choice = st.radio("Navigation", menu, horizontal=True)

# ------------ TIMER DISPLAY ------------
remaining = st.session_state.event_end - datetime.now()
if remaining.total_seconds() <= 0:
    st.warning("Event time is over.")
    remaining_str = "00:00:00"
else:
    remaining_str = str(remaining).split(".")[0]
st.write("⏱️ Time Left:", remaining_str)

event_active = remaining.total_seconds() > 0

# ------------ DASHBOARD ------------
if choice == "Dashboard":
    st.info(
        "Centralised platform for registrations, structured judging, live rankings, "
        "and instant certificate generation for CSE hackathons."
    )
    sub = load_submissions_df()
    ev = load_evaluations_df()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Teams", len(sub))
    c2.metric("Total Evaluations", len(ev))
    unique_judges = ev["judge"].nunique() if not ev.empty else 0
    c3.metric("Active Judges", unique_judges)

# ------------ TEAM SUBMISSION ------------
if choice == "Team Submission":
    if not event_active:
        st.error("Submissions are closed. Event time is over.")
    else:
        t = st.text_input("Team Name")
        m = st.text_area("Members")
        d = st.text_input("Domain")
        i = st.text_area("Idea / Problem Statement")

        if st.button("Submit Idea"):
            t_clean = t.strip()
            if not t_clean:
                st.error("Team name is required.")
            else:
                sub_df = load_submissions_df()
                if not sub_df.empty and t_clean in sub_df["team_name"].tolist():
                    st.error("Team name already exists.")
                else:
                    add_submission(t_clean, m, d, i)
                    st.success("✅ Submission recorded")

# ------------ BULK TEAM IMPORT ------------
if choice == "Bulk Team Import":
    st.write("Use this template for bulk upload (do not change header names).")

    sample_df = pd.DataFrame(columns=["Team Name", "Members", "Domain", "Idea"])
    sample_buf = BytesIO()
    sample_df.to_excel(sample_buf, index=False)
    sample_buf.seek(0)

    st.download_button(
        "⬇️ Download Sample Template",
        data=sample_buf,
        file_name="hackathon_bulk_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    file = st.file_uploader("Upload Excel (.xlsx)")
    if file:
        df = pd.read_excel(file)
        st.dataframe(df)
        if st.button("Upload"):
            bulk_add_submissions(df)
            st.success("✅ Bulk data uploaded")

# ------------ EVALUATE (JUDGE TABLET MODE READY) ------------
if choice == "Evaluate":
    if not st.session_state.judge_name:
        st.error("Please log in as a judge first.")
    elif not event_active:
        st.error("Evaluation is closed. Event time is over.")
    else:
        df = load_submissions_df()
        if df.empty:
            st.warning("No teams available to evaluate.")
        else:
            st.write("Select a team and assign scores on each criterion (0–10).")
            team = st.selectbox("Team", df["team_name"])

            team_row = df[df["team_name"] == team].iloc[0]
            with st.expander("Team details", expanded=True):
                st.markdown(f"**Domain:** {team_row['domain']}")
                st.markdown(f"**Members:** {team_row['members']}")
                st.markdown(f"**Idea:** {team_row['idea']}")

            if has_evaluation(team, st.session_state.judge_name):
                st.warning("You have already evaluated this team.")
            else:
                idea = st.slider("Idea", 0, 10)
                innovation = st.slider("Innovation", 0, 10)
                tech = st.slider("Technical Implementation", 0, 10)
                pres = st.slider("Presentation", 0, 10)
                impact = st.slider("Impact / Usefulness", 0, 10)

                total = compute_score(idea, innovation, tech, pres, impact)
                st.info(f"Total Score (weighted): {total}")

                if st.button("Submit Score", use_container_width=True):
                    add_evaluation(
                        team,
                        st.session_state.judge_name,
                        idea,
                        innovation,
                        tech,
                        pres,
                        impact,
                        total,
                    )
                    st.success("✅ Evaluation submitted")

# ------------ LEADERBOARD ------------
if choice == "Leaderboard":
    df = get_leaderboard_df()
    if not df.empty:
        display_cols = ["team_name", "domain", "final_score"]
        st.dataframe(
            df[display_cols].rename(columns={
                "team_name": "Team Name",
                "domain": "Domain",
                "final_score": "Final Score",
            })
        )
        top = df.iloc[0]["team_name"]
        st.markdown(f"🏆 **Current Leader:** {top}")
        if st.session_state.prev_top_team != top:
            st.session_state.prev_top_team = top
            st.balloons()
    else:
        st.info("No evaluations yet.")

# ------------ CERTIFICATES ------------
if choice == "Certificates":
    st.write("Certificates can be customised with department logo, signatures, and additional text in future iterations.")
    df = load_submissions_df()
    if df.empty:
        st.info("No teams found.")
    else:
        team = st.selectbox("Select Team", df["team_name"])
        if st.button("Generate Certificate"):
            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4)
            styles = getSampleStyleSheet()
            story = [
                Paragraph("Certificate of Achievement", styles["Title"]),
                Spacer(1, 20),
                Paragraph(f"Awarded to <b>{team}</b>", styles["Normal"]),
            ]
            doc.build(story)
            buf.seek(0)
            st.download_button(
                "⬇️ Download Certificate",
                buf,
                f"{team}.pdf"
            )

# ------------ EVENT CONTROL ------------
if choice == "Event Control":
    mins = st.number_input("Set new evaluation window (minutes from now)", value=120)
    if st.button("Reset Timer"):
        st.session_state.event_end = datetime.now() + timedelta(minutes=mins)
        st.success("Timer reset successfully!")

# ------------ REPORTS & EXPORT ------------
if choice == "Reports & Export":
    st.subheader("Export data as Excel files for record keeping and analysis")

    sub = load_submissions_df()
    ev = load_evaluations_df()

    if st.button("Refresh Data"):
        st.cache_data.clear()
        sub = load_submissions_df()
        ev = load_evaluations_df()
        st.success("Data refreshed from database.")

    if not sub.empty:
        buf_sub = BytesIO()
        sub.to_excel(buf_sub, index=False)
        buf_sub.seek(0)
        st.download_button(
            "⬇️ Download Submissions.xlsx",
            data=buf_sub,
            file_name="submissions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    if not ev.empty:
        buf_ev = BytesIO()
        ev.to_excel(buf_ev, index=False)
        buf_ev.seek(0)
        st.download_button(
            "⬇️ Download Evaluations.xlsx",
            data=buf_ev,
            file_name="evaluations.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
