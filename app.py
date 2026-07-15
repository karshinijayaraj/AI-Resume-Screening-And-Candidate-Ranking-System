import re
import json

import streamlit as st
import PyPDF2
import pandas as pd

from skills import skills

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="AI Resume Screening System",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Resume Screening & Candidate Ranking System")

# -----------------------------
# Job Description Input
# -----------------------------
job_desc = st.text_area(
    "Enter Job Description",
    height=150,
    placeholder="Example: Looking for a Python Developer with SQL, Machine Learning, Pandas, NumPy and Power BI skills."
)

# -----------------------------
# Resume Upload
# -----------------------------
uploaded_files = st.file_uploader(
    "Upload Resume PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

# -----------------------------
# PDF Text Extraction
# -----------------------------
def extract_text(pdf_file):
    """Returns (raw_text, lower_text). raw_text keeps original casing
    so we can pull a readable name; lower_text is used for skill matching."""
    raw_text = ""

    try:
        reader = PyPDF2.PdfReader(pdf_file)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                raw_text += page_text + "\n"

    except Exception as e:
        st.error(f"Error reading {pdf_file.name}: {e}")

    return raw_text, raw_text.lower()


# -----------------------------
# Candidate Email Extraction
# -----------------------------
def extract_email(raw_text):
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", raw_text)
    return match.group(0) if match else "Not found"


# -----------------------------
# Candidate Name Extraction
# -----------------------------
def extract_name(raw_text, filename):
    """Best-effort guess: first non-empty line that looks like a name
    (mostly letters/spaces, not too long). Falls back to the filename."""
    for line in raw_text.splitlines():
        line = line.strip()

        if not line:
            continue

        letters_only = re.sub(r"[^a-zA-Z]", "", line)

        if (
            2 <= len(line.split()) <= 4
            and len(letters_only) >= 4
            and len(line) <= 40
            and "@" not in line
            and not any(char.isdigit() for char in line)
        ):
            return line.title()

    # Fallback: use the filename without extension
    return filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()


# -----------------------------
# AI Summary Generator
# -----------------------------
def generate_summary(found_skills, score):

    if score >= 80:
        level = "Strong Candidate"
        recommendation = "Hire Immediately"

    elif score >= 70:
        level = "Good Candidate"
        recommendation = "Schedule Interview"

    elif score >= 50:
        level = "Average Candidate"
        recommendation = "Keep for Review"

    else:
        level = "Needs Improvement"
        recommendation = "Not Recommended"

    summary = f"""
Candidate possesses skills in: {', '.join(found_skills)}

Overall Assessment: {level}

Suitable Roles:
• Data Analyst
• Python Developer
• AI/ML Intern

Recruiter Recommendation:
{recommendation}
"""

    return summary, recommendation


# -----------------------------
# Gmail Automation (send emails directly to selected candidates)
# -----------------------------
def send_emails_via_gmail(gmail_user, gmail_app_password, candidates, subject_template, body_template):
    """candidates: list of dicts with Name/Email/Match Score (%)/Status.
    Sends one email per candidate using their info to fill the templates.
    Returns (sent_count, failed_list)."""
    import smtplib
    from email.mime.text import MIMEText

    sent = 0
    failed = []

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_app_password)

        for c in candidates:
            to_email = c.get("Email", "")

            if not to_email or to_email == "Not found":
                failed.append(f"{c.get('Name', 'Unknown')} (no email found)")
                continue

            context = {
                "name": c.get("Name", ""),
                "email": to_email,
                "score": c.get("Match Score (%)", ""),
                "status": c.get("Status", ""),
            }

            try:
                subject = subject_template.format(**context)
                body = body_template.format(**context)

                msg = MIMEText(body)
                msg["Subject"] = subject
                msg["From"] = gmail_user
                msg["To"] = to_email

                server.sendmail(gmail_user, [to_email], msg.as_string())
                sent += 1

            except Exception as e:
                failed.append(f"{c.get('Name', 'Unknown')} ({e})")

    return sent, failed


# -----------------------------
# Main Logic
# -----------------------------
if uploaded_files and job_desc:

    jd_skills = []

    for skill in skills:
        if skill.lower() in job_desc.lower():
            jd_skills.append(skill)

    results = []

    for file in uploaded_files:

        raw_text, resume_text = extract_text(file)

        name = extract_name(raw_text, file.name)
        email = extract_email(raw_text)

        found_skills = []

        for skill in skills:
            if skill.lower() in resume_text:
                found_skills.append(skill)

        if len(jd_skills) > 0:
            match_count = len(set(found_skills) & set(jd_skills))
            score = (match_count / len(jd_skills)) * 100
        else:
            score = 0

        missing_skills = list(set(jd_skills) - set(found_skills))

        if score >= 80:
            status = "Selected ✅"

        elif score >= 50:
            status = "Consider ⚠️"

        else:
            status = "Rejected ❌"

        # Feedback
        if score >= 80:
            feedback = "Excellent match for the job role."

        elif score >= 50:
            feedback = (
                "Good candidate but needs additional skills: "
                + ", ".join(missing_skills)
            )

        else:
            feedback = (
                "Candidate lacks most required skills. Needs training in: "
                + ", ".join(missing_skills)
            )

        summary, recommendation = generate_summary(
            found_skills,
            score
        )

        results.append({
            "Resume": file.name,
            "Name": name,
            "Email": email,
            "Match Score (%)": round(score, 2),
            "Status": status,
            "Skills Found": ", ".join(found_skills),
            "Missing Skills": ", ".join(missing_skills),
            "Feedback": feedback,
            "Recommendation": recommendation,
            "Summary": summary
        })

    # -----------------------------
    # DataFrame
    # -----------------------------
    df = pd.DataFrame(results)

    df = df.sort_values(
        by="Match Score (%)",
        ascending=False
    ).reset_index(drop=True)

    # -----------------------------
    # Dashboard
    # -----------------------------
    st.subheader("📊 Dashboard")

    total = len(df)

    selected = len(
        df[df["Status"].str.contains("Selected")]
    )

    consider = len(
        df[df["Status"].str.contains("Consider")]
    )

    rejected = len(
        df[df["Status"].str.contains("Rejected")]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Resumes", total)
    col2.metric("Selected", selected)
    col3.metric("Consider", consider)
    col4.metric("Rejected", rejected)

    # -----------------------------
    # Rankings
    # -----------------------------
    st.subheader("🏆 Candidate Rankings")

    st.dataframe(
        df.drop(columns=["Summary"]),
        use_container_width=True
    )

    # -----------------------------
    # Top Candidate
    # -----------------------------
    st.subheader("🌟 Top Candidate")

    top_candidate = df.iloc[0]

    st.success(
        f"""
Resume: {top_candidate['Resume']}

Name: {top_candidate['Name']}

Score: {top_candidate['Match Score (%)']}%

Status: {top_candidate['Status']}
"""
    )

    # -----------------------------
    # Resume Shortlisting Report
    # -----------------------------
    st.subheader("📋 Resume Shortlisting Report")

    st.write("### ✅ Selected Candidates")
    selected_df = df[df["Status"].str.contains("Selected")]

    if len(selected_df) > 0:
        st.dataframe(
            selected_df[["Resume", "Name", "Email", "Match Score (%)"]],
            use_container_width=True
        )
    else:
        st.write("No selected candidates.")

    st.write("### ⚠️ Consider Candidates")
    consider_df = df[df["Status"].str.contains("Consider")]

    if len(consider_df) > 0:
        st.dataframe(
            consider_df[["Resume", "Name", "Email", "Match Score (%)"]],
            use_container_width=True
        )
    else:
        st.write("No consider candidates.")

    st.write("### ❌ Rejected Candidates")
    rejected_df = df[df["Status"].str.contains("Rejected")]

    if len(rejected_df) > 0:
        st.dataframe(
            rejected_df[["Resume", "Name", "Email", "Match Score (%)"]],
            use_container_width=True
        )
    else:
        st.write("No rejected candidates.")

    # -----------------------------
    # Candidate Analysis
    # -----------------------------
    st.subheader("📝 Candidate Analysis")

    for i, row in df.iterrows():

        with st.expander(
            f"{row['Resume']} - {row['Match Score (%)']}%"
        ):

            st.write(f"**Name:** {row['Name']}")

            st.write(f"**Email:** {row['Email']}")

            st.write(f"**Status:** {row['Status']}")

            st.write(
                f"**Skills Found:** {row['Skills Found']}"
            )

            st.write(
                f"**Missing Skills:** {row['Missing Skills']}"
            )

            st.write(
                f"**Feedback:** {row['Feedback']}"
            )

            st.write(
                f"**Recommendation:** {row['Recommendation']}"
            )

            st.write("**Summary:**")

            st.write(
                row['Summary']
            )

    # -----------------------------
    # Download CSV
    # -----------------------------
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download Results CSV",
        data=csv,
        file_name="candidate_rankings.csv",
        mime="text/csv"
    )

    # -----------------------------
    # Gmail Automation: Email Selected Candidates directly
    # -----------------------------
    st.subheader("📧 Email Selected Candidates via Gmail")

    st.caption(
        "Sends an email straight from your Gmail account to every "
        "'Selected ✅' candidate — no Google Sheet or n8n workflow needed."
    )

    with st.expander("Gmail connection settings"):
        st.caption(
            "Use a Gmail **App Password**, not your normal password. "
            "Generate one at myaccount.google.com → Security → 2-Step "
            "Verification → App passwords (2-Step Verification must be ON)."
        )

        gmail_user = st.text_input(
            "Your Gmail address",
            placeholder="you@gmail.com",
            key="gmail_user"
        )

        gmail_app_password = st.text_input(
            "Gmail App Password",
            type="password",
            placeholder="16-character app password",
            key="gmail_app_password"
        )

        subject_template = st.text_input(
            "Email subject",
            value="You've been shortlisted!"
        )

        body_template = st.text_area(
            "Email body",
            height=180,
            value=(
                "Hi {name},\n\n"
                "Thank you for applying! Based on our screening, you've "
                "been shortlisted for the next stage (match score: "
                "{score}%).\n\n"
                "Our team will reach out shortly to schedule the next "
                "steps.\n\n"
                "Best regards,\nRecruiting Team"
            )
        )

        st.caption(
            "Placeholders available: {name}, {email}, {score}, {status}"
        )

        if st.button("📤 Send Emails to Selected Candidates Now"):
            if not gmail_user:
                st.error("Please enter your Gmail address.")
            elif not gmail_app_password:
                st.error("Please enter your Gmail App Password.")
            elif len(selected_df) == 0:
                st.warning("There are no Selected candidates to email.")
            else:
                try:
                    candidates = selected_df[
                        ["Name", "Email", "Match Score (%)", "Status"]
                    ].to_dict("records")

                    sent, failed = send_emails_via_gmail(
                        gmail_user,
                        gmail_app_password,
                        candidates,
                        subject_template,
                        body_template
                    )

                    st.success(
                        f"✅ Sent {sent} email(s) to selected candidate(s)."
                    )

                    if failed:
                        st.warning(
                            "⚠️ Could not send to: " + "; ".join(failed)
                        )

                except Exception as e:
                    st.error(f"Failed to send emails: {e}")

else:
    st.info(
        "Enter a Job Description and upload one or more resume PDFs."
    )
