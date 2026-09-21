# Architecture Notes

## Goal

The service demonstrates a layered backend for tracking job applications without storing real private application data in the public repository. Version 0.2 extends the initial MVP with protected access, paginated queries, and pipeline analytics.

## Components

```text
Client / Swagger UI
        │
        ▼
FastAPI route layer
        │
        ├── Pydantic validation
        ├── domain errors (404 / 409)
        ├── optional X-API-Key guard
        │
        ▼
Service/query layer
        │
        ▼
SQLAlchemy ORM
        │
        ├── SQLite (local/tests)
        └── PostgreSQL (Docker)
```

### HTTP layer

`app/api/routes/` owns transport concerns: path/query parameters, response models, status codes, and dependency injection.

### Schemas

`app/schemas/` separates API contracts from persistence models. This prevents ORM objects from becoming the public API by accident and provides validation at the service boundary.

### Persistence

The initial schema has four tables:

- `employers`
- `resume_versions`
- `applications`
- `status_history`

Applications reference an employer and optionally a resume version. Status-history rows reference one application and are deleted with it.

### Current-status denormalization

`applications.status` stores the current state while `status_history` stores the transition log. This duplicates the latest status intentionally:

- filtering current pipelines stays simple and fast;
- audit/history remains available;
- the write endpoint updates both in one transaction.

For a larger system, this invariant would be enforced more formally in a service layer and tested at the database boundary.

## Search, pagination, and analytics

The service uses SQL filtering instead of loading records into Python. Search spans:

- role title;
- employer name;
- location.

Structured filters cover status, work mode, employer, term length, and deadline windows.

The existing list endpoint still returns an array. The new `/applications/page` endpoint uses the same filtered query to calculate a total, applies a whitelisted sort column and ID tie-breaker, and returns `has_more` for pagination. `deadline` sorting puts null values last. Offset pagination is simple but can shift as records are inserted; cursor pagination would be appropriate at larger scale.

`/analytics/pipeline` uses grouped SQL counts and bounded deadline queries. Rejected, withdrawn, and closed applications are treated as terminal and excluded from overdue/upcoming deadline counts. The report accepts an explicit timezone-aware `as_of` value so tests and comparisons are reproducible. PostgreSQL full-text search or trigram indexes would be reasonable later if the dataset became large.

## Access model

When `API_KEY` is configured, every `/api/v1` route requires the `X-API-Key` header; the root and health routes remain public. Comparison is constant-time. Production mode fails at startup if the key is absent. Docker Compose binds the API to `127.0.0.1` for keyless local use. This is a **single-user guard**, not identity, role-based access, rate limiting, or secure multi-user isolation. A real deployment needs proper authentication and authorization before accepting private records.

## Error handling

Known domain failures use a stable JSON shape:

```json
{
  "error": {
    "code": "not_found",
    "message": "Application 42 was not found"
  }
}
```

The same shape is used for uniqueness conflicts. FastAPI/Pydantic still owns malformed-request validation and returns HTTP 422.

## Database initialization

`Base.metadata.create_all()` still keeps first-run setup simple. It does not version or alter existing schemas; Alembic migrations are the next database-hardening step. Do not treat the API-key guard as making this database lifecycle production-ready.

## Privacy model

This public repository should contain only:

- code;
- synthetic seed/demo records;
- architecture/API docs;
- non-sensitive test data.

It should never contain real resumes, transcripts, application PDFs, emails, credentials, or database dumps.

## Tradeoffs / next steps

1. **Alembic:** version schema changes instead of auto-creating tables.
2. **Authentication:** unnecessary for a local single-user portfolio demo, required for multi-user deployment.
3. **Frontend:** small dashboard consuming the API.
4. **Observability:** structured logs and request IDs.
5. **Stronger tests:** PostgreSQL integration test in CI in addition to isolated SQLite tests.
