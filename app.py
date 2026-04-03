import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from datetime import datetime

# -----------------------------
# JUDGE CONFIG
# -----------------------------
JUDGES = ["Judge 1", "Judge 2", "Judge 3"]

CRITERIA = {
    "Innovation": 0.3,
    "Technical Complexity": 0.3,
    "Presentation": 0.2,
    "Impact": 0.2
}

# -----------------------------
# SESSION STATE
# -----------------------------
if "locked" not in st.session_state:
    st.session_state.locked = False

st.title("🏆 Hackathon Judging Panel")

team_name = st.text_input("Enter Team Name")

scores = {}

# -----------------------------
# INPUT SCORES
# -----------------------------
if not st.session_state.locked:
    for judge in JUDGES:
        st.subheader(judge)
        scores[judge] = {}
        
        for crit in CRITERIA:
            scores[judge][crit] = st.slider(
                f"{judge} - {crit}",
                0, 10, 5
            )

# -----------------------------
# LOCK BUTTON
# -----------------------------
if st.button("🔒 Lock Scores"):
    st.session_state.locked = True
    st.success("Scores Locked!")

# -----------------------------
# CALCULATE FINAL SCORE
# -----------------------------
def calculate_score(scores):
    final_scores = []

    for judge in scores:
        total = 0
        for crit in CRITERIA:
            total += scores[judge][crit] * CRITERIA[crit]
        final_scores.append(total)

    return round(sum(final_scores) / len(final_scores), 2)

if st.session_state.locked:
    final_score = calculate_score(scores)

    st.success(f"Final Score: {final_score}")

# -----------------------------
# PDF GENERATION
# -----------------------------
def generate_pdf(team, score):
    file_name = f"{team}_report.pdf"

    doc = SimpleDocTemplate(file_name, pagesize=letter)
    elements = []

    elements.append(Paragraph(f"Team: {team}", None))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Final Score: {score}", None))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated on: {datetime.now()}", None))

    doc.build(elements)
    return file_name

if st.session_state.locked:
    if st.button("📄 Generate PDF Report"):
        pdf = generate_pdf(team_name, final_score)

        with open(pdf, "rb") as f:
            st.download_button(
                label="Download Report",
                data=f,
                file_name=pdf,
                mime="application/pdf"
            )
