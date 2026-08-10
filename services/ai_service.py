"""
AI extraction service.

PHASE 4: turns what the patient actually said into structured fields
(symptom, severity, associated issue, time of day) using an LLM.

IMPORTANT SAFETY RULE:
The model is instructed to NEVER diagnose, NEVER infer a medical condition,
and NEVER add anything the patient did not say. If the patient says
"my chest feels heavy", we store that literal phrase as the symptom -
never "heart problem" or any other inferred condition.

If LLM_API_KEY is missing, or the API call fails for any reason, this
raises AIExtractionError. app.py catches that and falls back to the
Phase 3 manual step-by-step questions, so the app never crashes and
never blocks the check-in.
"""

import json
import os

from dotenv import load_dotenv

load_dotenv()

EXTRACTION_SYSTEM_PROMPT = """You convert an elderly patient's own words about \
how they are feeling into a structured, patient-reported health event.

STRICT RULES:
- Never diagnose a disease or medical condition.
- Never infer what a symptom might mean medically. If the patient says \
"my chest feels heavy," the symptom is "chest heaviness" - never "heart problem."
- Never add any detail the patient did not say.
- Keep symptom wording close to the patient's own words, just tidied up \
(lowercase, no extra punctuation).
- If the patient did not mention a severity, associated issue, or time of \
day, use null for that field. Do not guess.

Respond with ONLY a JSON object, nothing else, no markdown fences, in \
exactly this shape:
{"symptom": "<short phrase>", "severity": <integer 1-10 or null>, \
"associated_issue": "<short phrase or null>", \
"time_of_day": "<morning|afternoon|evening|night or null>"}
"""


class AIExtractionError(Exception):
    """Raised whenever extraction can't be completed - missing key, API
    error, or a response that isn't valid JSON in the expected shape."""


def _get_client():
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise AIExtractionError("LLM_API_KEY is not set")

    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise AIExtractionError("anthropic package not installed") from e

    return Anthropic(api_key=api_key)


def extract_health_event(raw_text: str) -> dict:
    """
    Returns a dict: {"symptom": str, "severity": int|None,
    "associated_issue": str|None, "time_of_day": str|None}

    Raises AIExtractionError on any failure - missing key, network error,
    or a malformed response - so the caller can fall back gracefully.
    """
    client = _get_client()

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": raw_text}],
        )
    except Exception as e:
        raise AIExtractionError(f"LLM call failed: {e}") from e

    text_out = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    # Be tolerant of accidental ```json fences even though we asked for none
    if text_out.startswith("```"):
        text_out = text_out.strip("`")
        if text_out.startswith("json"):
            text_out = text_out[4:]
        text_out = text_out.strip()

    try:
        data = json.loads(text_out)
    except json.JSONDecodeError as e:
        raise AIExtractionError(f"Model did not return valid JSON: {e}") from e

    if "symptom" not in data or not data["symptom"]:
        raise AIExtractionError("Model response missing a symptom field")

    return {
        "symptom": str(data.get("symptom")).strip(),
        "severity": data.get("severity") or None,
        "associated_issue": data.get("associated_issue") or None,
        "time_of_day": data.get("time_of_day") or None,
    }
