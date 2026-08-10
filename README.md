# Continuity 🩺

**"Doctors see patients for minutes. Continuity remembers the days in between."**

A voice-first AI health companion for elderly people. Continuity records what a
patient reports day-to-day between doctor visits, and turns it into a clear,
honest longitudinal summary for the next appointment.

## ⚠️ What this is NOT

Continuity never diagnoses a disease, never prescribes or changes medicine,
and never claims to verify that a medicine was physically taken. It only
records and organizes what the patient says, in the patient's own words.

## Status

This repo currently has **Phase 1** built: a basic Streamlit UI shell with
navigation between Home, Daily Check-in, Health Timeline, Doctor Report,
Medicines, and Appointments. No database, AI, or voice yet — that comes in
later phases.

---

## STEP 1 — Install Python

Check if you already have Python 3.10+ installed:

```bash
python3 --version
```

If you don't have it, download it from https://www.python.org/downloads/
(any 3.10 or newer works).

## STEP 2 — Create the project folder

If you're starting from the files provided, just `cd` into the `continuity`
folder you downloaded. If you're starting fresh:

```bash
mkdir continuity
cd continuity
```

## STEP 3 — Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

You'll know it worked because your terminal prompt now starts with `(venv)`.

## STEP 4 — Install dependencies

```bash
pip install -r requirements.txt
```

## STEP 5 — Files

For Phase 1 you should have:

```
continuity/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
└── data/
    └── .gitkeep
```

## STEP 6 — Environment variables

Phase 1 doesn't need any API keys yet. Later phases will need a `.env` file:

```bash
cp .env.example .env
```

Then fill in keys as we add each service. Never commit `.env` — it's already
in `.gitignore`.

## STEP 7 — Run the app

```bash
streamlit run app.py
```

This opens the app in your browser (usually `http://localhost:8501`).

## STEP 8 — What to check right now

- Sidebar navigation switches between the 6 pages
- Home page shows the greeting, a disabled microphone button, and synthetic
  "next medicine" / "next appointment" info
- Nothing crashes, no errors in the terminal

Once you confirm this works, tell me and we'll move to **Phase 2** (SQLite
database for patient profile + health events).

---

## Setting up Git and pushing to GitHub

## STEP 9 — Initialize Git locally

From inside the `continuity` folder:

```bash
git init
git add .
git commit -m "Phase 1: basic Streamlit UI shell"
```

## STEP 10 — Create a GitHub repo

1. Go to https://github.com/new
2. Name it `continuity` (or whatever you like)
3. Leave it **empty** — don't check "Add a README" (you already have one)
4. Click **Create repository**

## STEP 11 — Connect and push

GitHub will show you a remote URL like
`https://github.com/YOUR_USERNAME/continuity.git`. Use it here:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/continuity.git
git push -u origin main
```

## STEP 12 — Ongoing workflow

After each phase, from the `continuity` folder:

```bash
git add .
git commit -m "Phase X: short description of what changed"
git push
```

`.gitignore` already keeps `.env`, the local database, and virtual
environment folders out of the repo, so it's safe to `git add .` freely —
just double-check `git status` before committing if you're ever unsure.

---

## Roadmap (later phases)

| Phase | What it adds |
|---|---|
| 2 | SQLite patient profile + health events |
| 3 | Text-based daily check-in |
| 4 | AI extraction of structured health events |
| 5 | Qdrant semantic memory (with SQLite fallback) |
| 6 | Voice input (browser speech recognition or Whisper) |
| 7 | Voice output (Rime, with browser TTS fallback) |
| 8 | Medicine reminders |
| 9 | Doctor-ready longitudinal report |
| 10 | "Load Shanti Demo" + "Simulate Next Appointment" demo mode |

## Medical safety limitations

Continuity is a patient-reported symptom log, not a medical device. It does
not diagnose, does not recommend treatment, and does not verify medication
adherence — it only records what the patient says they experienced or did.
All reports are for the patient and doctor to interpret together.
