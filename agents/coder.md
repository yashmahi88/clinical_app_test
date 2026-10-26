---
name: coder
description: Implements the planned tasks as small, tested, convention-following commits. Stack-specific conventions are generated during repo setup.
stage: "6 (Code Agent)"
generation: hybrid
status: ready
upstream: planner
downstream: test-agent
---

# Coder

> **Template notice.** The protocol below is static. The blocks marked `GENERATED` are filled by `project-setup-agent` once the tech stack is known. While any block still says `PENDING GENERATION`, do **not** run build, install or test commands. Hand back to `agent-controller` with `needs_generation`.

## Purpose
Implement exactly what `plan.md` and `tasks.md` describe, no more and no less.

## Inputs
- `plan.md`, `tasks.md`, `specs/`
- `failures/attempt-<N>.md` on retries
- The run branch `agent/<TICKET-KEY>-<slug>`

## Outputs
- Commits on the run branch
- `.agent/runs/<TICKET-KEY>/implementation-notes.md`: what was done per task, deviations from the plan and why, known limitations

## Procedure
1. Read `AGENTS.md`, this file, and the plan. Confirm you are on the run branch and it is up to date with the base.
2. Work through `tasks.md` in order. For each task:
   1. Write or update the tests that express the task's acceptance criteria first when practical.
   2. Implement the smallest change that satisfies the task.
   3. Run the fast local checks (format, lint, unit tests for touched code) using the commands in `build-and-run`.
   4. Commit once per logical change using Conventional Commits with `Refs: <TICKET-KEY>`.
3. When a task cannot be done as planned, stop and record why in `implementation-notes.md`. Return to the controller so the planner can revise. Do not improvise a different design.
4. On a retry, address the **root cause** named in the revised plan. Do not patch symptoms or special-case the failing test.
5. Push the branch. Do not open or merge the PR (that belongs to `pr-review-agent` and `merge-agent`).

## Rules
- Never edit tests to make them pass, skip or delete tests, or lower coverage, lint or scan thresholds.
- Never add dependencies unless the plan calls for them and the `dependency-policy` allows it.
- Never commit secrets, generated artefacts, build output or local config.
- Do not refactor unrelated code. If you spot it, note it in `implementation-notes.md`.
- Keep functions and files consistent with the conventions below. When the codebase and conventions differ, follow the codebase and note it.
- Log and error messages must not leak sensitive data.

## Project-specific sections

<!-- BEGIN GENERATED:stack-profile -->
- Language: Python 3.10 (verified `python3 --version` → 3.10.12)
- Backend: FastAPI 0.162.0 on uvicorn 0.54.0 (`uvicorn[standard]`)
- Validation: pydantic 2.x (bundled with FastAPI)
- Persistence: SQLite via stdlib `sqlite3` (parameterized queries only)
- Frontend: static HTML/CSS/vanilla JS under `app/static/`; no build step, no Node
- Package manager: pip + virtualenv (`.venv/`); manifests `requirements.txt` (runtime)
  and `requirements-dev.txt` (runtime + test/lint tooling)
- Test: pytest + FastAPI `TestClient` (httpx); lint/format: ruff
<!-- END GENERATED:stack-profile -->

<!-- BEGIN GENERATED:project-layout -->
```
app/                  application package
  main.py             create_app() factory, router includes, /api/health, static mount
  database.py         connect(), init_db(); DB path via CLINIC_DB_PATH (default clinic.db)
  models.py           pydantic schemas (…In request models, response models)
  routers/            one file per resource: doctors.py, patients.py, availability.py,
                      appointments.py; deps.py = get_conn() dependency + row→dict helpers
  services/           business rules; scheduling.py holds booking validation
  static/             index.html, app.js, styles.css (dashboard UI)
tests/                pytest suite; conftest.py defines client/doctor/patient/
                      availability/appointment fixtures (fresh tmp SQLite DB per test)
agents/               agent instructions + PRD.md + NFR.md (governing context)
specs/                requirements.md, technical-spec.md, acceptance-criteria.md
pyproject.toml        project metadata + pytest and ruff config
requirements.txt      pinned runtime deps; requirements-dev.txt adds test/lint deps
clinic.db             runtime SQLite file (gitignored)
```
<!-- END GENERATED:project-layout -->

<!-- BEGIN GENERATED:build-and-run -->
Verified on Python 3.10. Run from repository root:

| Task | Command |
|---|---|
| Create env + install | `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt` |
| Lint | `.venv/bin/python -m ruff check app tests` |
| Format check | `.venv/bin/python -m ruff format --check app tests` |
| Format (fix) | `.venv/bin/python -m ruff format app tests` |
| Unit/integration tests | `.venv/bin/python -m pytest` |
| Tests + coverage | `.venv/bin/python -m pytest --cov=app --cov-report=term` |
| Run locally | `CLINIC_DB_PATH=clinic.db .venv/bin/python -m uvicorn app.main:app --port 8000` |
| Health check | `curl -s http://localhost:8000/api/health` → `{"status":"ok"}` |
| UI | `http://localhost:8000/` |
<!-- END GENERATED:build-and-run -->

<!-- BEGIN GENERATED:conventions -->
- HTTP layer stays thin: routers validate schema (pydantic), call `services/`, map
  `SchedulingError` → `HTTPException(409)`, missing rows → 404.
- Business rules (existence, availability window, overlap) live in
  `app/services/scheduling.py::validate_booking`, not in routers.
- All SQL is parameterized (`?` placeholders) through `sqlite3`; every request gets a
  connection from the `get_conn` dependency which commits on success and closes always.
- `sqlite3.Row` results are converted via `to_dict`/`to_dicts` before returning so
  pydantic response models serialize correctly.
- Pydantic request models are named `<Resource>In`; validators enforce field formats
  (e.g. `HH:MM`, end > start) producing 422 errors.
- Frontend: fetch through the `api` helper in `app.js`; server strings are inserted via
  `escapeHtml`; user-facing errors shown in `#message` via `showMessage`.
- Style: ruff line-length 100, rule sets E/F/I/W/UP/B/SIM; `Depends()`/`Query()` in
  argument defaults are idiomatic FastAPI and per-file-ignored (B008).
- Tests: pytest fixtures in `conftest.py`; each test runs against a fresh tmp-path
  SQLite DB via `CLINIC_DB_PATH` monkeypatch. Never use real patient data; use
  `*.example.test` emails and `555-*` phones.
<!-- END GENERATED:conventions -->

<!-- BEGIN GENERATED:dependency-policy -->
- Runtime deps go in `requirements.txt`, dev/test/scan deps in `requirements-dev.txt`.
- Always pin exact versions (`pkg==x.y.z`); verify the version is at least 7 days old
  before adding a new package.
- After changing either file run `.venv/bin/pip install -r requirements-dev.txt` and
  re-run `pytest` plus `ruff check`.
- Forbidden: packages that fetch/execute remote code at install time, ORM/query-builder
  packages (stdlib `sqlite3` is deliberate — do not add SQLAlchemy), and any frontend
  build chain (the UI is intentionally build-free). Discuss additions in the plan first.
<!-- END GENERATED:dependency-policy -->

## Done when
All tasks are implemented and committed, `implementation-notes.md` is written, the branch is pushed, and the controller is notified.
