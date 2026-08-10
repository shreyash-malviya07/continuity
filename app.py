"""
CONTINUITY - Voice-first AI health companion for elderly people.

PHASE 3: text-based daily check-in conversation.
The patient now goes through a real question-by-question conversation
(feeling -> symptom -> severity -> associated issue -> time of day ->
confirm), and nothing is saved until they confirm the summary is correct.
This is still rule-based, not AI - Phase 4 replaces the structured
questions with real extraction from free-form text.
"""

import datetime

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
from services.checkin_service import (
    CheckinState,
    new_checkin,
    receive_feeling,
    apply_extraction,
    fall_back_to_manual,
    submit_symptom,
    submit_severity,
    submit_associated,
    submit_time,
    confirm_edit,
)
from services.ai_service import extract_health_event, AIExtractionError

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

    if "checkin" not in st.session_state:
        st.session_state.checkin = new_checkin()
    state: CheckinState = st.session_state.checkin

    if st.session_state.get("checkin_ai_error"):
        st.warning(
            "AI extraction is unavailable right now "
            f"({st.session_state.checkin_ai_error}), so we're asking a "
            "few quick questions instead."
        )
        del st.session_state["checkin_ai_error"]

    # Render conversation so far as chat bubbles
    for role, text in state.history:
        with st.chat_message("assistant" if role == "ai" else "user"):
            st.write(text)

    # Render the input for whichever step we're on
    if state.step == "feeling":
        with st.form("feeling_form"):
            text = st.text_area("Your answer", placeholder=(
                "e.g. My knee is hurting again today, around a 7 out of 10, "
                "and I had difficulty walking this morning."
            ))
            if st.form_submit_button("Send") and text.strip():
                receive_feeling(state, text)
                with st.spinner("Thinking..."):
                    try:
                        extracted = extract_health_event(state.feeling_text)
                        apply_extraction(state, extracted)
                    except AIExtractionError as e:
                        st.session_state.checkin_ai_error = str(e)
                        fall_back_to_manual(state)
                st.rerun()

    elif state.step == "symptom":
        with st.form("symptom_form"):
            text = st.text_input("Your answer", placeholder="knee pain")
            if st.form_submit_button("Send") and text.strip():
                submit_symptom(state, text)
                st.rerun()

    elif state.step == "severity":
        with st.form("severity_form"):
            severity = st.slider("Severity (0 = not applicable)", 0, 10, 0)
            if st.form_submit_button("Send"):
                submit_severity(state, severity)
                st.rerun()

    elif state.step == "associated":
        with st.form("associated_form"):
            text = st.text_input("Your answer (optional)",
                                  placeholder="difficulty walking")
            if st.form_submit_button("Send"):
                submit_associated(state, text)
                st.rerun()

    elif state.step == "time":
        with st.form("time_form"):
            time_of_day = st.selectbox(
                "Your answer (optional)",
                ["", "morning", "afternoon", "evening", "night"],
            )
            if st.form_submit_button("Send"):
                submit_time(state, time_of_day)
                st.rerun()

    elif state.step == "confirm":
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm"):
                event = HealthEvent(
                    id=None,
                    date=datetime.date.today().isoformat(),
                    symptom=state.symptom,
                    severity=state.severity if state.severity > 0 else None,
                    associated_issue=state.associated_issue or None,
                    time_of_day=state.time_of_day or None,
                    source="patient_reported",
                    raw_text=state.feeling_text,
                )
                add_health_event(event)
                st.session_state.checkin = new_checkin()
                st.success("Recorded. Thank you.")
                st.rerun()
        with col2:
            if st.button("✏️ Edit"):
                confirm_edit(state)
                st.rerun()

    if state.history:
        st.divider()
        if st.button("Start a new check-in"):
            st.session_state.checkin = new_checkin()
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
st.sidebar.caption("Continuity — Phase 3: text-based daily check-in conversation.")
