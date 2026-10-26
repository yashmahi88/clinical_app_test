# Non-Functional Requirements — Clinical Appointment Manager

Ticket: ADO-19923. Measurable constraints; each item states how it is checked.

## 1. Security

- **NFR-S1** All SQL is executed through parameterized queries (`sqlite3` `?` placeholders).
  No string-formatted SQL with user input. Checked by code review and ruff rules.
- **NFR-S2** All request bodies are validated by pydantic schemas before any business logic.
  Checked by `pytest` (422 cases) and FastAPI response models.
- **NFR-S3** Frontend escapes all server-returned values inserted into the DOM
  (`escapeHtml` in `app/static/app.js`); no `innerHTML` with raw API data. Checked by review.
- **NFR-S4** No credentials, tokens or `.env` files are committed. Checked by repository
  inspection and the secret scanner configured in `agents/security-scanning-agent.md`.
- **NFR-S5** Patient data is synthetic only (test fixtures use `*.example.test` addresses,
  `555-*` phone numbers). Checked by fixture review and AC9.
- **NFR-S6** Dependencies are pinned to exact versions in `requirements.txt` /
  `requirements-dev.txt` and scanned for known vulnerabilities (`pip-audit`, when available).

## 2. Performance

- **NFR-P1** API list endpoints respond in under 200 ms for up to 10,000 appointment rows
  on the reference SQLite database. Checked by manual timing / profiling if challenged.
- **NFR-P2** Overlap and availability checks are O(availability windows + matching
  appointments) per request; no full-table scans beyond an indexed `doctor_id` filter.
- **NFR-P3** Frontend assets are static files served without build tooling; total JS+CSS
  payload under 100 KB.

## 3. Reliability

- **NFR-R1** All writes commit through a single connection-per-request dependency
  (`get_conn`); failed requests close the connection without partial commits.
- **NFR-R2** Schema is created idempotently (`CREATE TABLE IF NOT EXISTS`) at startup;
  restarts never lose or duplicate data. Checked by `test_persistence_across_restart`.
- **NFR-R3** Double-booking cannot occur: the overlap check runs inside the same request
  transaction as the insert. (Single-process SQLite write serialization applies.)
- **NFR-R4** `GET /api/health` returns `{"status": "ok"}` whenever the process is up;
  used for liveness and smoke checks.

## 4. Accessibility and usability

- **NFR-A1** Every form input has an associated `<label>`; the message area uses
  `role="alert"`. Checked by markup review.
- **NFR-A2** Validation failures produce human-readable messages both in the browser
  (HTML5 `reportValidity`) and from the API (`detail` field surfaced in the UI).

## 5. Observability

- **NFR-O1** The application runs under uvicorn, which emits access logs (method, path,
  status, latency) on stdout for every request.
- **NFR-O2** Monitoring uses `GET /api/health` (liveness) and HTTP 5xx rate from access
  logs as primary signals, per `agents/monitoring-agent.md`.

## 6. Privacy

- **NFR-PR1** The system stores only synthetic patient data; no real PHI is permitted.
- **NFR-PR2** Logs and error messages must not include patient records; API errors return
  generic messages (`detail` strings contain rule violations, not record contents).

## 7. Maintainability

- **NFR-M1** Modular layout: `app/routers/` (HTTP), `app/services/` (business rules),
  `app/models.py` (schemas), `app/database.py` (persistence), `app/static/` (UI).
- **NFR-M2** `ruff check` and `ruff format --check` pass with zero findings; configured in
  `pyproject.toml` (line length 100, rule sets E, F, I, W, UP, B, SIM).
- **NFR-M3** The pytest suite passes (`tests/`), covering every endpoint and every
  scheduling rule; new behavior ships with tests in the same change.
- **NFR-M4** Coverage target: ≥ 80% of statements (pipeline default), measured with
  `pytest --cov=app` when `pytest-cov` is installed.
