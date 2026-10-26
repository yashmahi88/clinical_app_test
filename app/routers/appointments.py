import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models import Appointment, AppointmentIn, RescheduleIn
from app.routers.deps import get_conn, to_dict, to_dicts
from app.services.scheduling import SchedulingError, validate_booking

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.get("", response_model=list[Appointment])
def list_appointments(
    day: date | None = Query(default=None, description="Filter to a single date (YYYY-MM-DD)"),
    status: str | None = Query(default=None, pattern="^(booked|cancelled)$"),
    conn: sqlite3.Connection = Depends(get_conn),
):
    query = "SELECT * FROM appointments WHERE 1=1"
    params: list = []
    if day is not None:
        query += " AND date(start) = date(?)"
        params.append(day.isoformat())
    if status is not None:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY start"
    return to_dicts(conn.execute(query, params).fetchall())


@router.post("", response_model=Appointment, status_code=201)
def create_appointment(body: AppointmentIn, conn: sqlite3.Connection = Depends(get_conn)):
    try:
        validate_booking(conn, body.doctor_id, body.patient_id, body.start, body.end)
    except SchedulingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    cur = conn.execute(
        "INSERT INTO appointments (doctor_id, patient_id, start, end) VALUES (?, ?, ?, ?)",
        (body.doctor_id, body.patient_id, body.start.isoformat(), body.end.isoformat()),
    )
    return {"id": cur.lastrowid, "status": "booked", **body.model_dump()}


@router.put("/{appointment_id}", response_model=Appointment)
def reschedule_appointment(
    appointment_id: int, body: RescheduleIn, conn: sqlite3.Connection = Depends(get_conn)
):
    row = conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if row["status"] == "cancelled":
        raise HTTPException(status_code=409, detail="Cannot reschedule a cancelled appointment")
    try:
        validate_booking(
            conn,
            row["doctor_id"],
            row["patient_id"],
            body.start,
            body.end,
            exclude_appointment_id=appointment_id,
        )
    except SchedulingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    conn.execute(
        "UPDATE appointments SET start = ?, end = ? WHERE id = ?",
        (body.start.isoformat(), body.end.isoformat(), appointment_id),
    )
    return to_dict(
        conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
    )


@router.delete("/{appointment_id}", response_model=Appointment)
def cancel_appointment(appointment_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    row = conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    conn.execute("UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,))
    return to_dict(
        conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
    )
