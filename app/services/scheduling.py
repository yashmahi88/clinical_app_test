import sqlite3
from datetime import datetime


class SchedulingError(Exception):
    """Raised when an appointment violates scheduling rules."""


def _require_row(conn: sqlite3.Connection, table: str, row_id: int, label: str) -> None:
    if conn.execute(f"SELECT 1 FROM {table} WHERE id = ?", (row_id,)).fetchone() is None:
        raise SchedulingError(f"{label} {row_id} does not exist")


def validate_booking(
    conn: sqlite3.Connection,
    doctor_id: int,
    patient_id: int,
    start: datetime,
    end: datetime,
    exclude_appointment_id: int | None = None,
) -> None:
    """Enforce: doctor/patient exist, slot is within doctor availability,
    and no overlapping non-cancelled appointment exists for the doctor."""
    _require_row(conn, "doctors", doctor_id, "Doctor")
    _require_row(conn, "patients", patient_id, "Patient")

    weekday = start.weekday()
    if end.date() != start.date():
        raise SchedulingError("Appointment must start and end on the same day")

    windows = conn.execute(
        "SELECT start_time, end_time FROM availability WHERE doctor_id = ? AND weekday = ?",
        (doctor_id, weekday),
    ).fetchall()
    start_t, end_t = start.strftime("%H:%M"), end.strftime("%H:%M")
    if not any(w["start_time"] <= start_t and end_t <= w["end_time"] for w in windows):
        raise SchedulingError("Appointment is outside the doctor's availability")

    query = (
        "SELECT 1 FROM appointments WHERE doctor_id = ? AND status = 'booked' "
        "AND start < ? AND end > ?"
    )
    params: list = [doctor_id, end.isoformat(), start.isoformat()]
    if exclude_appointment_id is not None:
        query += " AND id != ?"
        params.append(exclude_appointment_id)
    if conn.execute(query, params).fetchone() is not None:
        raise SchedulingError("Appointment overlaps an existing booking for this doctor")
