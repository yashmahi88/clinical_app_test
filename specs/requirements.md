# Requirements — Clinical Appointment Manager (ADO-19923)

1. Manage doctors and their specializations (create, list).
2. Register patients using synthetic information only (name, email, phone).
3. Configure recurring weekly doctor availability windows (weekday, start/end time).
4. Book, reschedule, and cancel appointments for a doctor and patient.
5. Prevent overlapping appointments for the same doctor (cross-doctor overlaps allowed).
6. Reject bookings outside availability, spanning multiple days, or with end ≤ start.
7. Display appointments on a dashboard with doctor, patient, time and status.
8. Filter appointments by date and by status.
9. Persist all data (SQLite file; survives restart).
10. Validate input on frontend and backend; return clear error messages.
