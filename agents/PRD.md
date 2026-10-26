# Product Requirements Document — Clinical Appointment Manager

Ticket: ADO-19923. Governing context for all work in this repository.

## 1. Product goal

A medical appointment management platform for clinic reception staff. Receptionists use it to
manage doctors and their specializations, register patients, configure doctor availability, and
book, reschedule and cancel appointments through a web dashboard.

## 2. Users

- **Clinic reception staff** — the only user role. They perform all scheduling operations.
  No authentication or role management is required for this version (single-receptionist
  deployment behind a trusted network is assumed).

## 3. Scope

In scope:

- Doctor management: create and list doctors with a specialization.
- Patient registration: create and list patients using **synthetic information only**.
- Availability configuration: weekly recurring availability windows per doctor
  (weekday + start/end time).
- Appointment lifecycle: book, reschedule, cancel.
- Conflict prevention: overlapping appointments for the same doctor are rejected.
- Dashboard: list appointments, filter by date and by status.
- Persistence: all data survives application restart (SQLite file).
- Validation: input validated on the frontend (HTML5 constraints) and the backend
  (pydantic + scheduling rules).

Out of scope (exclusions):

- Diagnosis, medical advice, prescriptions, or treatment recommendations of any kind.
- Real patient data. The system is for synthetic/test data only.
- Authentication, authorization, user accounts, multi-clinic support.
- Billing, insurance, reminders/notifications to patients.
- Doctor self-service portal or patient-facing portal.

## 4. Requirements

| # | Requirement |
|---|---|
| R1 | Create and list doctors with a name and specialization. |
| R2 | Register and list patients (name, email, phone) using synthetic data. |
| R3 | Configure recurring weekly availability windows per doctor. |
| R4 | Book an appointment for a doctor and patient within a configured availability window. |
| R5 | Reschedule an existing (non-cancelled) appointment to a new valid slot. |
| R6 | Cancel an appointment (record retained with status `cancelled`). |
| R7 | Reject any appointment that overlaps an existing non-cancelled appointment for the same doctor. Overlaps for *different* doctors are permitted. Adjacent (touching) slots are permitted. |
| R8 | Reject appointments outside the doctor's availability, spanning multiple days, or with end ≤ start. |
| R9 | Dashboard lists all appointments with doctor, patient, start, end, status. |
| R10 | Filter the appointment list by a single date and/or by status (`booked`, `cancelled`). |
| R11 | Persist all data in a SQLite database; data survives restart. |
| R12 | Validate input on the frontend (required fields, formats) and backend (422 schema validation, 409 scheduling conflicts, 404 missing resources). |

## 5. Acceptance criteria

| # | Criterion | Verified by |
|---|---|---|
| AC1 | Working frontend and backend | `uvicorn app.main:app` serves `/` (UI) and `/api/*`; `GET /api/health` returns 200 |
| AC2 | Users can create doctors and patients | `tests/test_doctors_patients.py`, UI forms |
| AC3 | Appointments book within doctor availability | `test_book_appointment_within_availability` |
| AC4 | Conflicting appointments are rejected | `test_overlapping_appointment_rejected`, `test_booking_outside_availability_rejected` |
| AC5 | Appointments can be rescheduled and cancelled | `test_reschedule_*`, `test_cancel_*` |
| AC6 | Data persists after restart | `test_persistence_across_restart` |
| AC7 | Automated tests cover core scheduling behavior | `pytest` suite in `tests/` |
| AC8 | Build, lint, and test commands pass | `pip install -r requirements-dev.txt`, `ruff check`, `ruff format --check`, `pytest` |
| AC9 | No credentials or real patient information committed | repository inspection; fixtures use `*.example.test` synthetic data |

## 6. API surface (implemented)

| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/api/doctors`, GET `/api/doctors/{id}` | Manage doctors |
| GET/POST | `/api/patients`, GET `/api/patients/{id}` | Register patients |
| GET/POST | `/api/availability` (`?doctor_id=`) | Weekly availability windows |
| GET/POST | `/api/appointments` (`?day=`, `?status=`) | List/filter and book |
| PUT | `/api/appointments/{id}` | Reschedule |
| DELETE | `/api/appointments/{id}` | Cancel (sets status, keeps record) |
| GET | `/api/health` | Health check |
| GET | `/` | Dashboard UI |

## 7. Error model

- `422` — schema validation failure (malformed fields, end ≤ start, bad weekday/time).
- `404` — referenced doctor, patient or appointment does not exist.
- `409` — scheduling rule violation: outside availability, overlapping booking,
  rescheduling a cancelled appointment, multi-day appointment.
