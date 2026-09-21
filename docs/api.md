# API Guide

Base prefix: `/api/v1`

Interactive documentation is generated automatically at `/docs`.

If `API_KEY` is configured, send `X-API-Key: <your key>` on all `/api/v1` requests; missing or incorrect keys return HTTP 401. The root and `/health` endpoints remain public. `APP_ENV=production` refuses to start without an API key. This is single-user protection, not multi-user authorization.

## Employers

### `POST /employers`

Creates an employer. Employer names are unique. Duplicate names return HTTP 409.

### `GET /employers`

Query parameters:

- `search` — case-insensitive partial name match
- `limit` — 1 to 100

## Resume versions

Resume-version records store **metadata only**. Do not upload actual resumes to this public service/repository.

### `POST /resume-versions`

Example:

```json
{
  "label": "Backend / Data Resume v1",
  "filename": "backend_data_resume_v1.pdf",
  "notes": "Synthetic metadata only; file is not stored in the repository."
}
```

### `GET /resume-versions`

Lists newest versions first.

## Applications

### `POST /applications`

Required fields:

- `employer_id`
- `role_title`

If `term_length_months` is supplied, `term_start` is required.
`deadline`, when supplied, must include a timezone offset (for example `Z` or `+00:00`).

Creating an application also creates its first status-history record.

### `GET /applications`

Supported filters:

| Parameter | Example | Purpose |
|---|---|---|
| `search` | `software` | role, employer, or location text |
| `status` | `applied` | current application status |
| `work_mode` | `hybrid` | onsite / hybrid / remote |
| `employer_id` | `3` | one employer |
| `location` | `Ottawa` | partial location match |
| `term_length_months` | `8` | exact placement length |
| `deadline_before` | ISO datetime | upcoming-deadline window |
| `deadline_after` | ISO datetime | lower deadline bound |
| `limit` | `50` | page size |
| `offset` | `0` | simple pagination offset |
| `sort_by` | `deadline` | `updated_at`, `created_at`, `deadline`, or `role_title` |
| `sort_order` | `asc` | `asc` or `desc` |

The response remains a JSON array for compatibility. Deadline filters must include timezone offsets, and an inverted deadline window returns HTTP 422. Sort columns are whitelisted; equal values are ordered by ID so page boundaries are deterministic.

### `GET /applications/page`

Accepts the same filters and sort parameters as `/applications` but returns pagination metadata:

```json
{
  "items": [{ "id": 1, "role_title": "Software Developer Intern" }],
  "total": 12,
  "limit": 1,
  "offset": 0,
  "has_more": true
}
```

The example `items` entry is abbreviated; actual entries use the full `ApplicationRead` schema. `has_more` is based on the filtered total, not on the current page length alone. Null deadlines sort last in both directions.

### `GET /applications/{id}`

Returns one application with nested employer and optional resume-version metadata.

### `PATCH /applications/{id}`

Updates editable application fields other than status. Unknown fields, explicit nulls for required fields, and naive deadline timestamps return HTTP 422. Use the status-history endpoint to change status so a transition record is preserved.

### `DELETE /applications/{id}`

Deletes an application and its status history.

## Status history

### `POST /applications/{id}/status-history`

```json
{
  "status": "interview",
  "note": "Synthetic example: first-round interview scheduled."
}
```

Updates the application's current status and appends a history row in the same transaction.

### `GET /applications/{id}/status-history`

Returns newest status records first.

## Pipeline analytics

### `GET /analytics/pipeline`

Parameters:

- `window_days` — 1–90, default 7;
- `as_of` — optional timezone-aware ISO timestamp, default current UTC time.

The response includes `total`, `active`, `by_status` (including zero counts), `overdue_deadlines`, `due_soon`, and up to ten `upcoming_deadlines` ordered by deadline then ID. Rejected, withdrawn, and closed applications are terminal and excluded from deadline counts. `due_soon` covers deadlines from `as_of` through the end of the window, inclusive; `overdue_deadlines` are earlier than `as_of`.

## Status values

- `interested`
- `preparing`
- `applied`
- `assessment`
- `interview`
- `offer`
- `rejected`
- `withdrawn`
- `closed`

## Work-mode values

- `onsite`
- `hybrid`
- `remote`
- `unspecified`
