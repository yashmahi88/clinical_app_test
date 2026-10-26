import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.models import Patient, PatientIn
from app.routers.deps import get_conn, to_dict, to_dicts

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=list[Patient])
def list_patients(conn: sqlite3.Connection = Depends(get_conn)):
    return to_dicts(conn.execute("SELECT * FROM patients ORDER BY name").fetchall())


@router.post("", response_model=Patient, status_code=201)
def create_patient(body: PatientIn, conn: sqlite3.Connection = Depends(get_conn)):
    cur = conn.execute(
        "INSERT INTO patients (name, email, phone) VALUES (?, ?, ?)",
        (body.name, body.email, body.phone),
    )
    return {"id": cur.lastrowid, **body.model_dump()}


@router.get("/{patient_id}", response_model=Patient)
def get_patient(patient_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return to_dict(row)
