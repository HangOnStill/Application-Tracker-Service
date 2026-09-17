# API Guide

Base prefix: `/api/v1`

Interactive documentation is generated automatically at `/docs`.

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

### `GET /applications/{id}`

Returns one application with nested employer and optional resume-version metadata.

### `PATCH /applications/{id}`

Updates editable application fields other than status. Use the status-history endpoint to change status so a transition record is preserved.

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
