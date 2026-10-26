import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.models import Doctor, DoctorIn
from app.routers.deps import get_conn, to_dict, to_dicts

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


@router.get("", response_model=list[Doctor])
def list_doctors(conn: sqlite3.Connection = Depends(get_conn)):
    return to_dicts(conn.execute("SELECT * FROM doctors ORDER BY name").fetchall())


@router.post("", response_model=Doctor, status_code=201)
def create_doctor(body: DoctorIn, conn: sqlite3.Connection = Depends(get_conn)):
    cur = conn.execute(
        "INSERT INTO doctors (name, specialization) VALUES (?, ?)",
        (body.name, body.specialization),
    )
    return {"id": cur.lastrowid, **body.model_dump()}


@router.get("/{doctor_id}", response_model=Doctor)
def get_doctor(doctor_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    row = conn.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return to_dict(row)
