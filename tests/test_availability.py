def test_create_and_list_availability(client, doctor):
    res = client.post(
        "/api/availability",
        json={"doctor_id": doctor["id"], "weekday": 2, "start_time": "08:00", "end_time": "12:00"},
    )
    assert res.status_code == 201

    items = client.get(f"/api/availability?doctor_id={doctor['id']}").json()
    assert items[0]["start_time"] == "08:00"


def test_availability_requires_existing_doctor(client):
    res = client.post(
        "/api/availability",
        json={"doctor_id": 999, "weekday": 0, "start_time": "09:00", "end_time": "10:00"},
    )
    assert res.status_code == 404


def test_availability_rejects_end_before_start(client, doctor):
    res = client.post(
        "/api/availability",
        json={"doctor_id": doctor["id"], "weekday": 0, "start_time": "12:00", "end_time": "09:00"},
    )
    assert res.status_code == 422


def test_availability_rejects_invalid_weekday(client, doctor):
    res = client.post(
        "/api/availability",
        json={"doctor_id": doctor["id"], "weekday": 7, "start_time": "09:00", "end_time": "10:00"},
    )
    assert res.status_code == 422
