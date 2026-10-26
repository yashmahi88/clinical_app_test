def test_create_and_list_doctors(client):
    res = client.post("/api/doctors", json={"name": "Dr. A", "specialization": "Dermatology"})
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Dr. A"
    assert body["id"] > 0

    listing = client.get("/api/doctors").json()
    assert any(d["id"] == body["id"] for d in listing)


def test_doctor_validation_rejects_empty_name(client):
    res = client.post("/api/doctors", json={"name": "", "specialization": "X"})
    assert res.status_code == 422


def test_get_missing_doctor_returns_404(client):
    assert client.get("/api/doctors/999").status_code == 404


def test_create_and_list_patients(client):
    res = client.post(
        "/api/patients",
        json={"name": "P", "email": "p@example.test", "phone": "555-0000"},
    )
    assert res.status_code == 201
    assert res.json()["id"] > 0
    assert len(client.get("/api/patients").json()) == 1


def test_patient_validation_rejects_bad_email(client):
    res = client.post(
        "/api/patients", json={"name": "P", "email": "not-an-email", "phone": "555-0000"}
    )
    assert res.status_code == 422
