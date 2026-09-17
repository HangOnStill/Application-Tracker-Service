# Architecture Notes

## Goal

The preliminary MVP demonstrates a small but defensible backend architecture for tracking job applications without storing real private application data in the public repository.

## Components

```text
Client / Swagger UI
        │
        ▼
FastAPI route layer
        │
        ├── Pydantic validation
        ├── domain errors (404 / 409)
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

## Search/filter strategy

The MVP uses SQL filtering instead of loading records into Python. Search spans:

- role title;
- employer name;
- location.

Structured filters cover status, work mode, employer, term length, and deadline windows.

This is sufficient for a portfolio MVP. PostgreSQL full-text search or trigram indexes would be reasonable later if the dataset became large.

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

For the preliminary version, `Base.metadata.create_all()` keeps first-run setup simple. This is deliberately documented as an MVP compromise. A production-ready next step is Alembic migrations.

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
3. **Metrics:** pipeline conversion and deadline summary endpoints.
4. **Frontend:** small dashboard consuming the API.
5. **Observability:** structured logs and request IDs.
6. **Stronger tests:** PostgreSQL integration test in CI in addition to isolated SQLite tests.
