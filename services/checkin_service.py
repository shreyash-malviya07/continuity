"""
Text-based daily check-in conversation flow.

PHASE 3: this is a fixed, rule-based sequence of questions - NOT an AI
conversation yet. The patient answers each question directly (feeling,
symptom name, severity, associated issue, time of day), then confirms
before anything is saved - matching the "confirm before saving" rule from
the spec. Phase 4 will replace the structured questions with real AI
extraction from free-form speech/text.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class CheckinState:
    step: str = "feeling"
    # steps in order: feeling -> symptom -> severity -> associated -> time -> confirm -> done
    history: List[Tuple[str, str]] = field(default_factory=list)  # (role, text)
    feeling_text: str = ""
    symptom: str = ""
    severity: int = 0          # 0 means "not reported"
    associated_issue: str = ""
    time_of_day: str = ""


def new_checkin() -> CheckinState:
    state = CheckinState()
    state.history.append(
        ("ai", "How are you feeling today? Tell me in your own words.")
    )
    return state


def submit_feeling(state: CheckinState, text: str) -> None:
    state.feeling_text = text.strip()
    state.history.append(("patient", state.feeling_text))
    state.history.append(
        ("ai", "What would you call this? For example, \"knee pain\" "
               "or \"headache\".")
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

    summary_lines = [f"I heard: {state.symptom}"]
    if state.severity > 0:
        summary_lines.append(f"rated {state.severity} out of 10")
    if state.associated_issue:
        summary_lines.append(f"with {state.associated_issue}")
    if state.time_of_day:
        summary_lines.append(f"in the {state.time_of_day}")
    summary = ", ".join(summary_lines) + ". Is that correct?"

    state.history.append(("ai", summary))
    state.step = "confirm"


def confirm_edit(state: CheckinState) -> None:
    """Patient said the summary is wrong - restart from the symptom question."""
    state.history.append(("patient", "Let me correct that."))
    state.history.append(
        ("ai", "No problem. What would you call this?")
    )
    state.step = "symptom"
