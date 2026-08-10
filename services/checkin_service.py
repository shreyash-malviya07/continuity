"""
Daily check-in conversation flow.

PHASE 4: the patient now only answers ONE open question ("How are you
feeling today?"). Their free-form answer is sent to services/ai_service.py
for extraction. If that succeeds, we go straight to confirm. If it fails
for any reason (no API key, network error, bad response), we fall back to
the Phase 3 step-by-step questions so the check-in still works.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class CheckinState:
    step: str = "feeling"
    # steps: feeling -> confirm (AI path)
    #     or feeling -> symptom -> severity -> associated -> time -> confirm (fallback)
    history: List[Tuple[str, str]] = field(default_factory=list)  # (role, text)
    feeling_text: str = ""
    symptom: str = ""
    severity: int = 0          # 0 means "not reported"
    associated_issue: str = ""
    time_of_day: str = ""
    used_ai: bool = False


def new_checkin() -> CheckinState:
    state = CheckinState()
    state.history.append(
        ("ai", "How are you feeling today? Tell me in your own words.")
    )
    return state


def _build_summary(state: CheckinState) -> str:
    parts = [f"I heard: {state.symptom}"]
    if state.severity:
        parts.append(f"rated {state.severity} out of 10")
    if state.associated_issue:
        parts.append(f"with {state.associated_issue}")
    if state.time_of_day:
        parts.append(f"in the {state.time_of_day}")
    return ", ".join(parts) + ". Is that correct?"


def receive_feeling(state: CheckinState, text: str) -> None:
    """Record the patient's free-text answer. Call this before attempting
    AI extraction or falling back, so the message shows in the chat either
    way."""
    state.feeling_text = text.strip()
    state.history.append(("patient", state.feeling_text))


def apply_extraction(state: CheckinState, extracted: dict) -> None:
    """AI extraction succeeded - go straight to confirm."""
    state.symptom = extracted["symptom"]
    state.severity = extracted.get("severity") or 0
    state.associated_issue = extracted.get("associated_issue") or ""
    state.time_of_day = extracted.get("time_of_day") or ""
    state.used_ai = True

    state.history.append(("ai", _build_summary(state)))
    state.step = "confirm"


def fall_back_to_manual(state: CheckinState) -> None:
    """AI extraction unavailable or failed - ask the Phase 3 questions
    one at a time instead."""
    state.used_ai = False
    state.history.append(
        ("ai", "I couldn't process that automatically, so let's go "
               "step by step. What would you call this? For example, "
               "\"knee pain\" or \"headache\".")
    )
    state.step = "symptom"


def submit_symptom(state: CheckinState, symptom: str) -> None:
    state.symptom = symptom.strip()
    state.history.append(("patient", state.symptom))
    state.history.append(
        ("ai", "On a scale of 1 to 10, how would you describe it? "
               "Choose 0 if that doesn't apply.")
    )
    state.step = "severity"


def submit_severity(state: CheckinState, severity: int) -> None:
    state.severity = severity
    display = f"{severity}/10" if severity > 0 else "Not applicable"
    state.history.append(("patient", display))
    state.history.append(
        ("ai", "Did you notice anything else, like difficulty walking "
               "or trouble sleeping? Leave it blank if not.")
    )
    state.step = "associated"


def submit_associated(state: CheckinState, associated: str) -> None:
    state.associated_issue = associated.strip()
    state.history.append(("patient", state.associated_issue or "Nothing else"))
    state.history.append(
        ("ai", "When did this happen - morning, afternoon, evening, "
               "or night? Leave it blank if unsure.")
    )
    state.step = "time"


def submit_time(state: CheckinState, time_of_day: str) -> None:
    state.time_of_day = time_of_day.strip()
    state.history.append(("patient", state.time_of_day or "Not sure"))
    state.history.append(("ai", _build_summary(state)))
    state.step = "confirm"


def confirm_edit(state: CheckinState) -> None:
    """Patient said the summary is wrong - restart from the symptom question."""
    state.history.append(("patient", "Let me correct that."))
    state.history.append(("ai", "No problem. What would you call this?"))
    state.step = "symptom"
