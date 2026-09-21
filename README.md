# Application Tracker Service

A portfolio backend for tracking job applications with **FastAPI**, **SQLAlchemy**, **PostgreSQL/SQLite**, automated tests, Docker, CI, and architecture/API documentation. Version 0.2 adds query metadata, pipeline analytics, and a configurable single-user API key without breaking the original list endpoint.

The project models the parts of an application search that become difficult to manage in spreadsheets: employers, applications, deadlines, status transitions, resume versions, and searchable records.

> **Portfolio status:** an evolving single-user service beyond the initial MVP, not a production job-search platform. The repository contains only synthetic/demo data—no real resumes, transcripts, credentials, or private application records.

## What this demonstrates

- Relational data modelling with foreign keys and uniqueness constraints.
- REST CRUD endpoints with request/response validation.
- Search and filtering across role, employer, location, status, deadline, and term length.
- Stable, whitelisted sorting and a paginated search response with total and `has_more` metadata.
- Pipeline summary with status counts, overdue deadlines, and upcoming deadlines.
- Optional `X-API-Key` protection for data routes; production mode refuses to start without a configured key.
- Explicit 404/409 API errors and transaction rollback on database conflicts.
- Status-history tracking instead of silently overwriting application progress.
- SQLite for zero-setup local/test use and PostgreSQL for Docker execution.
- Automated API tests with an isolated temporary database.
- GitHub Actions CI.
- Architecture and API documentation written for an engineering reviewer.

## Domain model

```text
Employer 1 ─── * Application * ─── 0..1 ResumeVersion
                       │
                       └── 1 ─── * StatusHistory
```

An `Application` stores the current status for efficient filtering; every explicit status change can also append a `StatusHistory` record for auditability.

## Repository structure

```text
Application-Tracker-Service/
├── app/
│   ├── api/routes/          # HTTP endpoints
│   ├── core/                # configuration + API errors
│   ├── db/                  # SQLAlchemy base/session
│   ├── models/              # relational ORM models
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # application query/filter logic
│   ├── main.py
│   └── seed.py
├── tests/                   # isolated API tests
├── docs/
│   ├── architecture.md
│   └── api.md
├── .github/workflows/ci.yml
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Quick start — local SQLite

Python 3.11+ is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

By default, local/demo mode has no API key. To guard the API, set `API_KEY` to a long random value in your untracked `.env` file and send it in the `X-API-Key` header. `/health` and `/` remain public. **`APP_ENV=production` requires `API_KEY`**, but this shared key is not multi-user authentication; do not expose real personal records through this demo service.

Seed synthetic demo records:

```powershell
python -m app.seed
```

## Quick start — Docker + PostgreSQL

```powershell
docker compose up --build
```

The API becomes available at `http://127.0.0.1:8000` and uses PostgreSQL inside Docker. Compose binds the API to loopback only so a keyless demo is not exposed to other devices on the network.

Stop the stack:

```powershell
docker compose down
```

Remove the local Docker database volume as well:

```powershell
docker compose down -v
```

## Example workflow

Create an employer:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/employers `
  -ContentType application/json `
  -Body '{"name":"Northstar Systems","website":"https://example.com"}'
```

Create an application using the returned employer `id`:

```json
{
  "employer_id": 1,
  "role_title": "Software Developer Intern",
  "location": "Ottawa, ON",
  "work_mode": "hybrid",
  "term_start": "2027-01-11",
  "term_length_months": 8,
  "status": "interested",
  "deadline": "2026-10-15T23:59:00Z",
  "application_url": "https://example.com/jobs/123",
  "language_requirement": "English"
}
```

Search/filter:

```text
GET /api/v1/applications?search=software&status=interested&work_mode=hybrid
GET /api/v1/applications?deadline_before=2026-11-01T00:00:00Z
GET /api/v1/applications?term_length_months=8&location=Ottawa
GET /api/v1/applications/page?search=software&limit=20&offset=0&sort_by=deadline&sort_order=asc
```

`/applications/page` returns `items`, `total`, `limit`, `offset`, and `has_more`. The original `/applications` list response remains available for compatibility. Sorting is limited to `updated_at`, `created_at`, `deadline`, and `role_title`; deadline timestamps and filters must include a timezone offset.

Pipeline snapshot:

```text
GET /api/v1/analytics/pipeline?window_days=7
```

It returns counts for every status, active-application and overdue-deadline totals, plus up to ten nearest open deadlines in the requested window. Use `as_of` with a timezone offset for reproducible reports, for example `as_of=2026-10-01T12:00:00Z`.

Record a status change:

```json
POST /api/v1/applications/1/status-history
{
  "status": "applied",
  "note": "Submitted through employer portal."
}
```

## Tests

```powershell
pytest
```

The tests use a temporary SQLite database and do not touch your local development database.

## Privacy and portfolio safety

Do **not** commit real applicant data to this public repository. Keep the following out of Git:

- `.env` files and tokens;
- real resumes and transcripts;
- application PDFs;
- database dumps;
- personal contact details beyond information intentionally published in the README/profile;
- employer correspondence or interview notes containing private information.

Use synthetic records in screenshots, tests, demos, and seed scripts.

## Current scope

Implemented:

- employers;
- resume-version metadata;
- applications;
- application search/filtering;
- status history;
- tests;
- Docker/PostgreSQL;
- CI;
- API/architecture docs;
- configurable single-user API key guard;
- paginated, sortable application search;
- pipeline and deadline analytics.

Remaining work before a production deployment:

1. Alembic database migrations.
2. Authentication and user ownership if the service becomes multi-user.
3. CSV import/export with explicit privacy and size controls.
4. Small frontend dashboard.
5. PostgreSQL integration coverage, rate limits, backups, and operational monitoring.

## Reviewer path

If you are reviewing this as a portfolio project, the fastest path is:

1. `app/models/application.py` — relational application model.
2. `app/api/routes/applications.py` — CRUD, filtering, and status-history API.
3. `app/services/applications.py` — filtered, sortable queries and page counts.
4. `app/api/routes/analytics.py` — grouped pipeline and deadline metrics.
5. `tests/test_advanced.py` — pagination, analytics, access, and validation behavior.
6. `docs/architecture.md` — design rationale and tradeoffs.
