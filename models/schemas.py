"""
Data shapes used across Continuity.

Kept as plain dataclasses (not an ORM) on purpose - this is a hackathon
MVP and SQLite rows map to these directly in database/db.py.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Patient:
    id: int
    name: str
    age: int
    condition: str
    doctor: str
    last_appointment: str          # ISO date string, e.g. "2026-08-01"
    next_appointment: str          # ISO date string
    next_appointment_time: str     # e.g. "11:00 AM"
    next_medicine_time: str        # e.g. "8:00 PM"


@dataclass
class HealthEvent:
    id: Optional[int]
    date: str                      # ISO date string
    symptom: str                   # e.g. "knee pain"
    severity: Optional[int]        # 1-10, or None if not reported
    associated_issue: Optional[str]  # e.g. "difficulty walking"
    time_of_day: Optional[str]     # e.g. "morning"
    source: str                    # always "patient_reported"
    raw_text: str                  # what the patient actually said
