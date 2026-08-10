"""
CONTINUITY - Voice-first AI health companion for elderly people.

PHASE 1: Basic Streamlit UI shell.
No database, no AI, no voice yet - just the navigation and screens
so we can see the app's skeleton and confirm it runs.
"""

import streamlit as st

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
# Hardcoded synthetic patient for Phase 1 (real DB comes in Phase 2)
# ----------------------------------------------------------------
DEMO_PATIENT = {
    "name": "Shanti Sharma",
    "age": 68,
    "condition": "Arthritis",
    "doctor": "Dr. Sharma",
    "last_appointment": "2026-08-01",
    "next_appointment": "2026-08-15",
    "next_appointment_time": "11:00 AM",
    "next_medicine_time": "8:00 PM",
}

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
    st.title(f"Good Morning, {DEMO_PATIENT['name'].split()[0]} 👋")
    st.subheader("How are you feeling today?")

    st.button("🎙️ MICROPHONE / TALK", disabled=True,
              help="Voice input arrives in a later phase")
    st.caption("(Voice input is not wired up yet - Phase 1 is UI only)")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Next medicine**")
        st.write(DEMO_PATIENT["next_medicine_time"])
    with col2:
        st.markdown("**Next appointment**")
        st.write(f"{DEMO_PATIENT['doctor']}")
        st.write(f"{DEMO_PATIENT['next_appointment']}, "
                  f"{DEMO_PATIENT['next_appointment_time']}")


def daily_checkin_page():
    st.title("Daily Check-in")
    st.info("This screen will let Shanti talk or type about how she's "
            "feeling. Coming in Phase 3 (text) and Phase 6 (voice).")
    st.text_area("For now, type freely here (not saved yet):",
                  placeholder="e.g. My knee is hurting again today...")


def timeline_page():
    st.title("Health Timeline")
    st.info("This will show the day-by-day patient-reported history "
            "once we add the database in Phase 2.")


def report_page():
    st.title("Doctor Report")
    st.info("The longitudinal doctor-ready report is built in Phase 9, "
            "once we have real events to summarize.")


def medicines_page():
    st.title("Medicines")
    st.info("Medicine reminders are added in Phase 8.")


def appointments_page():
    st.title("Appointments")
    st.markdown(f"**Last appointment:** {DEMO_PATIENT['last_appointment']}")
    st.markdown(f"**Next appointment:** {DEMO_PATIENT['next_appointment']} "
                f"at {DEMO_PATIENT['next_appointment_time']} "
                f"with {DEMO_PATIENT['doctor']}")
    st.caption("Editable appointment settings arrive in a later phase.")


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
st.sidebar.caption("Continuity — Phase 1 skeleton. Data shown is synthetic.")
