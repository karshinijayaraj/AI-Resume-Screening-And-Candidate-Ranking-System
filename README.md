# AI Resume Screening & Candidate Ranking System

## What's new in this version
- Extracts each candidate's **Name** and **Email** straight from their resume PDF (shown in the dashboard, expanders, and CSV).
- New **"Email Selected Candidates via Gmail"** panel at the bottom of the app — sends a personalized email directly from your Gmail account to every `Selected ✅` candidate. No Google Sheet or n8n workflow required.

## Run it locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Connect it to Gmail (one-time setup)
Gmail requires an **App Password** for apps like this (your normal password won't work if 2-Step Verification is on, and Google is phasing out "less secure app" access entirely).

1. Turn on **2-Step Verification** on your Google account: https://myaccount.google.com/security
2. Go to **App passwords**: https://myaccount.google.com/apppasswords
3. Create a new app password (name it something like "Resume Screener") and copy the 16-character code Google gives you.
4. In the app, open **"Gmail connection settings,"** enter your Gmail address and paste that app password in.
5. Edit the **subject** and **body** template if you like. You can use `{name}`, `{email}`, `{score}`, and `{status}` as placeholders — they'll be filled in per candidate.
6. Click **"📤 Send Emails to Selected Candidates Now."** Every candidate marked `Selected ✅` gets an email right away — no polling, no extra automation tool needed.

> Note: your Gmail address and app password are only used in-memory for that one SMTP session — they are not saved anywhere by the app.

## Files
- `app.py` — the Streamlit app
- `skills.py` — the skills keyword list used for matching
- `requirements.txt` — Python dependencies
