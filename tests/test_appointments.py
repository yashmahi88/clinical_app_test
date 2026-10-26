MONDAY = "2026-11-02"


def book(client, doctor, patient, start, end):
    return client.post(
        "/api/appointments",
        json={
            "doctor_id": doctor["id"],
            "patient_id": patient["id"],
            "start": start,
            "end": end,
        },
    )


def test_book_appointment_within_availability(appointment):
    assert appointment["status"] == "booked"
    assert appointment["id"] > 0


def test_booking_outside_availability_rejected(client, doctor, patient, availability):
    res = book(client, doctor, patient, f"{MONDAY}T18:00:00", f"{MONDAY}T18:30:00")
    assert res.status_code == 409
    assert "availability" in res.json()["detail"]


def test_booking_on_unavailable_weekday_rejected(client, doctor, patient, availability):
    # 2026-11-03 is a Tuesday; only Monday availability is configured.
    res = book(client, doctor, patient, "2026-11-03T10:00:00", "2026-11-03T10:30:00")
    assert res.status_code == 409


def test_overlapping_appointment_rejected(client, doctor, patient, appointment):
    res = book(client, doctor, patient, f"{MONDAY}T10:15:00", f"{MONDAY}T10:45:00")
    assert res.status_code == 409
    assert "overlaps" in res.json()["detail"]


def test_adjacent_appointment_allowed(client, doctor, patient, appointment):
    res = book(client, doctor, patient, f"{MONDAY}T10:30:00", f"{MONDAY}T11:00:00")
    assert res.status_code == 201


def test_overlap_check_scoped_per_doctor(client, doctor, patient, appointment):
    other = client.post("/api/doctors", json={"name": "Dr. B", "specialization": "ENT"}).json()
    client.post(
        "/api/availability",
        json={"doctor_id": other["id"], "weekday": 0, "start_time": "09:00", "end_time": "17:00"},
    )
    res = book(client, other, patient, f"{MONDAY}T10:15:00", f"{MONDAY}T10:45:00")
    assert res.status_code == 201


def test_cancel_appointment(client, appointment):
    res = client.delete(f"/api/appointments/{appointment['id']}")
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"


def test_cancelled_slot_can_be_rebooked(client, doctor, patient, appointment):
    client.delete(f"/api/appointments/{appointment['id']}")
    res = book(client, doctor, patient, f"{MONDAY}T10:15:00", f"{MONDAY}T10:45:00")
    assert res.status_code == 201


def test_reschedule_appointment(client, appointment):
    res = client.put(
        f"/api/appointments/{appointment['id']}",
        json={"start": f"{MONDAY}T14:00:00", "end": f"{MONDAY}T14:30:00"},
    )
    assert res.status_code == 200
    assert res.json()["start"].startswith(f"{MONDAY}T14:00")


def test_reschedule_into_conflict_rejected(client, doctor, patient, appointment):
    second = book(client, doctor, patient, f"{MONDAY}T11:00:00", f"{MONDAY}T11:30:00").json()
    res = client.put(
        f"/api/appointments/{second['id']}",
        json={"start": f"{MONDAY}T10:15:00", "end": f"{MONDAY}T10:45:00"},
    )
    assert res.status_code == 409


def test_reschedule_cancelled_rejected(client, appointment):
    client.delete(f"/api/appointments/{appointment['id']}")
    res = client.put(
        f"/api/appointments/{appointment['id']}",
        json={"start": f"{MONDAY}T14:00:00", "end": f"{MONDAY}T14:30:00"},
    )
    assert res.status_code == 409


def test_filter_by_date_and_status(client, doctor, patient, appointment):
    client.delete(f"/api/appointments/{appointment['id']}")
    book(client, doctor, patient, f"{MONDAY}T12:00:00", f"{MONDAY}T12:30:00")

    booked = client.get("/api/appointments?status=booked").json()
    cancelled = client.get("/api/appointments?status=cancelled").json()
    by_day = client.get(f"/api/appointments?day={MONDAY}").json()
    other_day = client.get("/api/appointments?day=2026-11-03").json()

    assert all(a["status"] == "booked" for a in booked)
    assert all(a["status"] == "cancelled" for a in cancelled)
    assert len(booked) == 1 and len(cancelled) == 1
    assert len(by_day) == 2 and other_day == []


def test_missing_doctor_rejected(client, patient, availability):
    res = book(client, {"id": 999}, patient, f"{MONDAY}T10:00:00", f"{MONDAY}T10:30:00")
    assert res.status_code == 409


def test_end_before_start_rejected(client, doctor, patient, availability):
    res = book(client, doctor, patient, f"{MONDAY}T10:30:00", f"{MONDAY}T10:00:00")
    assert res.status_code == 422


def test_missing_appointment_404(client):
    assert client.get("/api/appointments/999").status_code in (404, 405)
    assert client.delete("/api/appointments/999").status_code == 404


def test_persistence_across_restart(client, doctor, patient, appointment, monkeypatch, tmp_path):
    # Recreate the app against the same database file; data must survive.
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client2:
        items = client2.get("/api/appointments").json()
        assert any(a["id"] == appointment["id"] for a in items)
