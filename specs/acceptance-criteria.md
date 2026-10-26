# Acceptance Criteria — ADO-19923

1. The application has a working frontend and backend.
   → `uvicorn app.main:app`; `/` serves the dashboard; `GET /api/health` → 200.
2. Users can create doctors and patients.
   → `tests/test_doctors_patients.py`; POST `/api/doctors`, `/api/patients`.
3. Users can book appointments within doctor availability.
   → `test_book_appointment_within_availability`.
4. Conflicting appointments are rejected (overlap / outside availability).
   → `test_overlapping_appointment_rejected`, `test_booking_outside_availability_rejected`,
     `test_booking_on_unavailable_weekday_rejected` → HTTP 409.
5. Appointments can be rescheduled and cancelled.
   → `test_reschedule_appointment`, `test_cancel_appointment`; PUT and DELETE
     `/api/appointments/{id}`.
6. Data persists after restart.
   → `test_persistence_across_restart`; SQLite file `clinic.db`.
7. Automated tests cover core scheduling behavior.
   → `pytest` → 25 tests in `tests/`.
8. Build, lint, and test commands pass.
   → `pip install -r requirements-dev.txt`; `ruff check app tests`;
     `ruff format --check app tests`; `pytest`.
9. No credentials or real patient information are committed.
   → repository contains no secrets; fixtures use synthetic `*.example.test` data only.
