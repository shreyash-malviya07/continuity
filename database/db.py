"""
SQLite database layer for Continuity.

Everything the app knows about a patient and their patient-reported health
events lives here, plus a local fallback table for event embeddings used
by services/memory_service.py when Qdrant isn't configured or unreachable.
"""

import json
import sqlite3
import os
from typing import List, Optional, Tuple

from models.schemas import Patient, HealthEvent

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "continuity.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist yet. Safe to call every startup."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS patient (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            condition TEXT,
            doctor TEXT,
            last_appointment TEXT,
            next_appointment TEXT,
            next_appointment_time TEXT,
            next_medicine_time TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS health_event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symptom TEXT NOT NULL,
            severity INTEGER,
            associated_issue TEXT,
            time_of_day TEXT,
            source TEXT NOT NULL DEFAULT 'patient_reported',
            raw_text TEXT
        )
        """
    )

    # Local fallback for semantic memory (Phase 5) - only used when Qdrant
    # is not configured or unreachable. See services/memory_service.py.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS event_embedding (
            event_id INTEGER PRIMARY KEY,
            embedding TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def seed_default_patient_if_empty() -> None:
    """
    If there is no patient row yet, create one synthetic profile so the
    app has something to show. This is NOT the "Load Shanti Demo" button
    from Phase 10 - it's just so the app isn't empty on first run.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM patient")
    count = cur.fetchone()["c"]

    if count == 0:
        cur.execute(
            """
            INSERT INTO patient
                (name, age, condition, doctor, last_appointment,
                 next_appointment, next_appointment_time, next_medicine_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Shanti Sharma", 68, "Arthritis", "Dr. Sharma",
                "2026-08-01", "2026-08-15", "11:00 AM", "8:00 PM",
            ),
        )
        conn.commit()

    conn.close()


def get_patient() -> Optional[Patient]:
    """Phase 2 supports a single patient profile (fine for a hackathon demo)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patient ORDER BY id LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return Patient(
        id=row["id"], name=row["name"], age=row["age"],
        condition=row["condition"], doctor=row["doctor"],
        last_appointment=row["last_appointment"],
        next_appointment=row["next_appointment"],
        next_appointment_time=row["next_appointment_time"],
        next_medicine_time=row["next_medicine_time"],
    )


def update_patient(patient: Patient) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE patient
        SET name = ?, age = ?, condition = ?, doctor = ?,
            last_appointment = ?, next_appointment = ?,
            next_appointment_time = ?, next_medicine_time = ?
        WHERE id = ?
        """,
        (
            patient.name, patient.age, patient.condition, patient.doctor,
            patient.last_appointment, patient.next_appointment,
            patient.next_appointment_time, patient.next_medicine_time,
            patient.id,
        ),
    )
    conn.commit()
    conn.close()


def add_health_event(event: HealthEvent) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO health_event
            (date, symptom, severity, associated_issue, time_of_day,
             source, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.date, event.symptom, event.severity,
            event.associated_issue, event.time_of_day,
            event.source, event.raw_text,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_all_health_events() -> List[HealthEvent]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM health_event ORDER BY date ASC, id ASC")
    rows = cur.fetchall()
    conn.close()

    return [
        HealthEvent(
            id=row["id"], date=row["date"], symptom=row["symptom"],
            severity=row["severity"], associated_issue=row["associated_issue"],
            time_of_day=row["time_of_day"], source=row["source"],
            raw_text=row["raw_text"],
        )
        for row in rows
    ]


def clear_all_health_events() -> None:
    """Used by the demo-reset flow in a later phase; handy for testing now too."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM health_event")
    cur.execute("DELETE FROM event_embedding")
    conn.commit()
    conn.close()


def get_event_by_id(event_id: int) -> Optional[HealthEvent]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM health_event WHERE id = ?", (event_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return HealthEvent(
        id=row["id"], date=row["date"], symptom=row["symptom"],
        severity=row["severity"], associated_issue=row["associated_issue"],
        time_of_day=row["time_of_day"], source=row["source"],
        raw_text=row["raw_text"],
    )


def save_event_embedding(event_id: int, embedding: List[float]) -> None:
    """Local fallback storage for an event's embedding vector."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO event_embedding (event_id, embedding) VALUES (?, ?)",
        (event_id, json.dumps(embedding)),
    )
    conn.commit()
    conn.close()


def get_all_event_embeddings() -> List[Tuple[int, List[float]]]:
    """Local fallback: all stored (event_id, embedding) pairs."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT event_id, embedding FROM event_embedding")
    rows = cur.fetchall()
    conn.close()
    return [(row["event_id"], json.loads(row["embedding"])) for row in rows]
