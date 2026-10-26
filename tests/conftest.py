import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """TestClient backed by a fresh temporary SQLite database."""
    monkeypatch.setenv("CLINIC_DB_PATH", str(tmp_path / "test.db"))
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client:
        yield client


@pytest.fixture()
def doctor(client):
    return client.post(
        "/api/doctors", json={"name": "Dr. Synthetic", "specialization": "General"}
    ).json()


@pytest.fixture()
def patient(client):
    return client.post(
        "/api/patients",
        json={"name": "Test Patient", "email": "synthetic@example.test", "phone": "555-0100"},
    ).json()


@pytest.fixture()
def availability(client, doctor):
    # Covers Monday (weekday 0) 09:00-17:00.
    return client.post(
        "/api/availability",
        json={
            "doctor_id": doctor["id"],
            "weekday": 0,
            "start_time": "09:00",
            "end_time": "17:00",
        },
    ).json()


MONDAY = "2026-11-02"  # a Monday


@pytest.fixture()
def appointment(client, doctor, patient, availability):
    return client.post(
        "/api/appointments",
        json={
            "doctor_id": doctor["id"],
            "patient_id": patient["id"],
            "start": f"{MONDAY}T10:00:00",
            "end": f"{MONDAY}T10:30:00",
        },
    ).json()
