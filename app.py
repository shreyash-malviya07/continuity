"""
CONTINUITY - Voice-first AI health companion for elderly people.

PHASE 2: SQLite-backed patient profile + health events.
The patient profile is now real (stored in data/continuity.db) and you can
edit it. Health events have a real table too - Phase 2 includes a temporary
manual entry form so you can test storage before Phase 3/4 build the real
AI-driven check-in.
"""

import streamlit as st

from database.db import (
    init_db,
    seed_default_patient_if_empty,
    get_patient,
    update_patient,
    add_health_event,
    get_all_health_events,
)
from models.schemas import Patient, HealthEvent

# ----------------------------------------------------------------
# Page config - do this first, before any other st.* call
# ----------------------------------------------------------------
st.set_page_config(
    page_title="Continuity",
    page_icon="🩺",
    layout="centered",
)

# ----------------------------------------------------------------
# Elderly-friendly styling: bigger text, bigger buttons, high contrast
# ----------------------------------------------------------------
st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        font-size: 20px;
    }
    div.stButton > button {
        font-size: 22px;
        padding: 0.75em 1.5em;
        border-radius: 12px;
        width: 100%;
    }
    h1 {
        font-size: 40px !important;
    }
    h2 {
        font-size: 30px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------
# Database setup - runs every startup, safe to call repeatedly
# ----------------------------------------------------------------
init_db()
seed_default_patient_if_empty()

# ----------------------------------------------------------------
# Navigation
# ----------------------------------------------------------------
PAGES = [
    "Home",
    "Daily Check-in",
    "Health Timeline",
    "Doctor Report",
    "Medicines",
    "Appointments",
]

st.sidebar.title("Continuity 🩺")
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")


def home_page():
    patient = get_patient()

    st.title(f"Good Morning, {patient.name.split()[0]} 👋")
    st.subheader("How are you feeling today?")

    st.button("🎙️ MICROPHONE / TALK", disabled=True,
              help="Voice input arrives in a later phase")
    st.caption("(Voice input is not wired up yet - Phase 1/2 is UI + storage only)")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Next medicine**")
        st.write(patient.next_medicine_time)
    with col2:
        st.markdown("**Next appointment**")
        st.write(f"{patient.doctor}")
        st.write(f"{patient.next_appointment}, {patient.next_appointment_time}")

    st.divider()
    with st.expander("Edit patient profile"):
        with st.form("edit_profile_form"):
            name = st.text_input("Name", value=patient.name)
            age = st.number_input("Age", value=patient.age, min_value=0, max_value=120)
            condition = st.text_input("Condition", value=patient.condition or "")
            doctor = st.text_input("Doctor", value=patient.doctor or "")
            last_appt = st.text_input("Last appointment (YYYY-MM-DD)",
                                       value=patient.last_appointment or "")
            next_appt = st.text_input("Next appointment (YYYY-MM-DD)",
                                       value=patient.next_appointment or "")
            next_appt_time = st.text_input("Next appointment time",
                                            value=patient.next_appointment_time or "")
            next_med_time = st.text_input("Next medicine time",
                                           value=patient.next_medicine_time or "")

            submitted = st.form_submit_button("Save profile")
            if submitted:
                updated = Patient(
                    id=patient.id, name=name, age=int(age), condition=condition,
                    doctor=doctor, last_appointment=last_appt,
                    next_appointment=next_appt,
                    next_appointment_time=next_appt_time,
                    next_medicine_time=next_med_time,
                )
                update_patient(updated)
                st.success("Profile saved.")
                st.rerun()


def daily_checkin_page():
    st.title("Daily Check-in")
    st.info("The real AI-driven conversation check-in comes in Phase 3 "
            "(text) and Phase 4 (structured extraction). For now, use the "
            "manual test form below to confirm events save to the database.")

    with st.form("manual_event_form"):
        st.caption("Temporary manual entry — for testing Phase 2 storage only.")
        date = st.text_input("Date (YYYY-MM-DD)", placeholder="2026-08-10")
        symptom = st.text_input("Symptom", placeholder="knee pain")
        severity = st.slider("Severity (1-10, optional)", 0, 10, 0,
                              help="Leave at 0 if no severity was reported")
        associated = st.text_input("Associated issue (optional)",
                                    placeholder="difficulty walking")
        time_of_day = st.selectbox("Time of day (optional)",
                                    ["", "morning", "afternoon", "evening", "night"])
        raw_text = st.text_area("What the patient said",
                                 placeholder="My knee is hurting again today.")

        submitted = st.form_submit_button("Save event")
        if submitted:
            if not date or not symptom:
                st.error("Date and symptom are required.")
            else:
                event = HealthEvent(
                    id=None, date=date, symptom=symptom,
                    severity=severity if severity > 0 else None,
                    associated_issue=associated or None,
                    time_of_day=time_of_day or None,
                    source="patient_reported",
                    raw_text=raw_text,
                )
                add_health_event(event)
                st.success(f"Saved: {symptom} on {date}")
                st.rerun()


def timeline_page():
    st.title("Health Timeline")
    events = get_all_health_events()

    if not events:
        st.info("No health events recorded yet. Add one from Daily Check-in.")
        return

    for e in events:
        with st.container(border=True):
            st.markdown(f"**{e.date} — {e.symptom}**")
            details = []
            if e.severity:
                details.append(f"Severity: {e.severity}/10")
            if e.associated_issue:
                details.append(f"Also reported: {e.associated_issue}")
            if e.time_of_day:
                details.append(f"Time: {e.time_of_day}")
            if details:
                st.write(" · ".join(details))
            if e.raw_text:
                st.caption(f"\"{e.raw_text}\"")
            st.caption(f"Source: {e.source}")


def report_page():
    st.title("Doctor Report")
    st.info("The longitudinal doctor-ready report is built in Phase 9, "
            "once we have real events and trend detection in place.")


def medicines_page():
    st.title("Medicines")
    st.info("Medicine reminders are added in Phase 8.")


def appointments_page():
    patient = get_patient()
    st.title("Appointments")
    st.markdown(f"**Last appointment:** {patient.last_appointment}")
    st.markdown(f"**Next appointment:** {patient.next_appointment} "
                f"at {patient.next_appointment_time} with {patient.doctor}")
    st.caption("Edit these from the Home page under 'Edit patient profile'.")


PAGE_FUNCS = {
    "Home": home_page,
    "Daily Check-in": daily_checkin_page,
    "Health Timeline": timeline_page,
    "Doctor Report": report_page,
    "Medicines": medicines_page,
    "Appointments": appointments_page,
}

PAGE_FUNCS[page]()

st.sidebar.divider()
st.sidebar.caption("Continuity — Phase 2: real patient + event storage (SQLite).")
