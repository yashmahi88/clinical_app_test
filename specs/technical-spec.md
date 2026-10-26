# Technical Specification — Clinical Appointment Manager

## Stack profile

- Language: Python 3.10 (verified: `python3 --version` → 3.10.12)
- Backend framework: FastAPI 0.162.0 (pinned in `requirements.txt`)
- Server: uvicorn 0.54.0 (`uvicorn[standard]`)
- Validation: pydantic 2.14 (ships with FastAPI)
- Persistence: SQLite via stdlib `sqlite3` (parameterized queries; file `clinic.db`,
  override with `CLINIC_DB_PATH`)
- Frontend: static HTML/CSS/vanilla JS in `app/static/`, served by FastAPI
  (`FileResponse` + `StaticFiles`); no build step
- Package manager: pip; manifests `requirements.txt`, `requirements-dev.txt`
- Test framework: pytest 9.1.1 + FastAPI `TestClient` (httpx 0.28.1)
- Lint/format: ruff 0.17.2 (`ruff check`, `ruff format`), config in `pyproject.toml`
- Security scanning: pip-audit (dependencies, optional), gitleaks or `git grep` for
  secrets, ruff SAST subset; no Dockerfile or IaC present (n/a)
- CI: none configured in repository; commands are agent-run
- Deployment target: dev only (`environments.allowed: [dev]` in
  `.agent/config/pipeline.yml`); local uvicorn process
- Observability: uvicorn access logs on stdout; `GET /api/health` liveness endpoint

## Architecture

```
app/
  main.py             FastAPI app factory, static mount, /api/health
  database.py         sqlite3 connect() + idempotent schema init (CLINIC_DB_PATH)
  models.py           pydantic request/response schemas with validators
  routers/            one router per resource: doctors, patients, availability,
                      appointments; deps.py provides per-request connection
  services/
    scheduling.py     validate_booking(): existence, availability window, overlap
  static/             index.html, app.js, styles.css (dashboard + forms)
tests/                pytest suite, fixtures in conftest.py (fresh tmp SQLite DB)
```

Key decisions:

- Cancellation is a status change (`cancelled`), not a delete — record retained.
- Overlap rule: `existing.start < new.end AND existing.end > new.start`, scoped to
  `doctor_id` and `status='booked'`.
- Availability is recurring weekly (weekday 0–6), matched by `start.weekday()` and
  `HH:MM` string comparison (times stored as `HH:MM`).
- No authentication in this version (see PRD scope).

## Open questions

- Multi-clinic or multi-user access control if real deployment is ever required.
- Timezone handling: appointments are naive local datetimes; sufficient for a
  single-clinic tool.
