import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.models import Availability, AvailabilityIn
from app.routers.deps import get_conn, to_dicts

router = APIRouter(prefix="/api/availability", tags=["availability"])


@router.get("", response_model=list[Availability])
def list_availability(doctor_id: int | None = None, conn: sqlite3.Connection = Depends(get_conn)):
    if doctor_id is None:
        return to_dicts(
            conn.execute("SELECT * FROM availability ORDER BY doctor_id, weekday").fetchall()
        )
    return to_dicts(
        conn.execute(
            "SELECT * FROM availability WHERE doctor_id = ? ORDER BY weekday, start_time",
            (doctor_id,),
        ).fetchall()
    )


@router.post("", response_model=Availability, status_code=201)
def create_availability(body: AvailabilityIn, conn: sqlite3.Connection = Depends(get_conn)):
    if conn.execute("SELECT 1 FROM doctors WHERE id = ?", (body.doctor_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    cur = conn.execute(
        "INSERT INTO availability (doctor_id, weekday, start_time, end_time) VALUES (?, ?, ?, ?)",
        (body.doctor_id, body.weekday, body.start_time, body.end_time),
    )
    return {"id": cur.lastrowid, **body.model_dump()}
