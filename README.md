# Simplified DLP Platform

A small Data Loss Prevention backend. It manages keyword-based **Data Types** (inspection rules), groups them into **Data Sets** (policies), and **scans text** against a Data Set to report which rules fired.

Python 3.12 · FastAPI · PostgreSQL · SQLAlchemy 2.0 · Alembic · Docker Compose

## Quick start

Requirements: Docker with Docker Compose.

```bash
docker compose up --build
```

That's all the setup. Compose starts PostgreSQL, waits until it's healthy, applies the database migrations and starts the API.

| What | Where |
|---|---|
| API | http://localhost:8000 |
| Interactive docs (try every endpoint) | http://localhost:8000/docs |
| OpenAPI contract | http://localhost:8000/openapi.json |
| Health check (API + database) | http://localhost:8000/health |

**Tests** run inside the API container, against a separate `dlp_test` database that is created and migrated automatically:

```bash
docker compose run --rm api pytest
```

**Postman:** import [`postman/Simplified-DLP-Platform.postman_collection.json`](postman/Simplified-DLP-Platform.postman_collection.json) and click *Run collection*. It's a runnable tour (create Data Types → create a Data Set → scans → every error case → cleanup), with checks on each response. It can be re-run any number of times.

**Stop:** `docker compose down` (add `-v` to also delete the database volume).

Configuration comes only from environment variables. `docker-compose.yml` provides local defaults, and [`.env.example`](.env.example) documents them.

## API

| Method | Path | Description | Success |
|---|---|---|---|
| `GET` | `/api/datatypes?limit=50&offset=0` | List Data Types, sorted by name (max `limit` 200) | 200 |
| `POST` | `/api/datatypes` | Create a Data Type | 201 |
| `GET` | `/api/datatypes/{id}` | Get one Data Type | 200 |
| `PUT` | `/api/datatypes/{id}` | Replace a Data Type | 200 |
| `DELETE` | `/api/datatypes/{id}` | Delete a Data Type (refused while a Data Set uses it) | 204 |
| `GET` | `/api/datasets?limit=50&offset=0` | List Data Sets, sorted by name | 200 |
| `POST` | `/api/datasets` | Create a Data Set | 201 |
| `GET` | `/api/datasets/{id}` | Get one Data Set | 200 |
| `PUT` | `/api/datasets/{id}` | Replace a Data Set | 200 |
| `DELETE` | `/api/datasets/{id}` | Delete a Data Set | 204 |
| `POST` | `/api/scan` | Scan text against a Data Set | 200 |

**Data Type** (`POST /api/datatypes`):

```json
{
  "name": "Financial",
  "description": "HR compensation data",
  "type": "keywords",
  "content": ["salary", "bonus", "payroll"],
  "threshold": 2,
  "case_sensitive": false
}
```

`description` (default `""`) and `case_sensitive` (default `false`) are optional. **Data Set:** `{"name": "HR policy", "data_type_ids": ["<uuid>", "<uuid>"]}`.

**Scan:**

```bash
curl -X POST localhost:8000/api/scan -H 'content-type: application/json' \
  -d '{"dataset_id": "<uuid>", "text": "The salary and bonus numbers for Falcon are attached."}'
```

```json
{
  "status": "match",
  "detected_objects": [
    {"id": "1f15de28-...", "name": "Financial", "match_count": 2},
    {"id": "63fbb59c-...", "name": "Project Falcon", "match_count": 1}
  ]
}
```

When nothing fires, the response is exactly `{"status": "not matched"}`.

**Errors** use [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457) (`application/problem+json`) with a stable `code`:

```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "Cannot delete Data Type 3f2a...: used by 1 Data Sets",
  "code": "DATA_TYPE_IN_USE",
  "dataset_ids": ["9c1d..."]
}
```

| Status | When |
|---|---|
| 400 `MALFORMED_JSON` | The body isn't valid JSON |
| 404 `DATA_TYPE_NOT_FOUND` / `DATASET_NOT_FOUND` | The id in the URL doesn't exist |
| 409 `DUPLICATE_NAME` | A name is already taken |
| 409 `DATA_TYPE_IN_USE` | Deleting a Data Type that Data Sets reference (their ids are listed) |
| 422 `VALIDATION_ERROR` | Invalid field values, unknown fields or wrong types (submitted values are never echoed back) |
| 422 `UNKNOWN_DATA_TYPES` | A Data Set references Data Type ids that don't exist (they're listed) |
| 422 `UNKNOWN_DATASET` | Scanning against a Data Set that doesn't exist |

## How matching works

Each Data Type in the Data Set is evaluated **independently**. Its `match_count` is the number of keyword occurrences in the text, and it **fires when `match_count ≥ threshold`**. The scan is a `match` if **any** Data Type fires (OR logic), and `detected_objects` lists only the ones that fired, strongest first.

## Key design decisions

The spec leaves several behaviors open. Each one was resolved explicitly; the full log with options and rationale is in [`docs/DECISIONS.md`](docs/DECISIONS.md).

| Question | Decision |
|---|---|
| Case sensitivity | Case-insensitive by default (changing case must not bypass a rule). An optional per-Data-Type `case_sensitive` flag handles acronyms. (D-005) |
| What is a whole word? | Letters and digits form words, and everything else separates them, including `_`. `salary_2024.xlsx` and `customer_salary` match `salary`; `salaryman` doesn't. (D-007) |
| What does "keyword count" count? | Every occurrence: `salary salary` counts 2. (D-006) |
| Overlapping keywords (`credit`, `credit card`) | One regex per Data Type, longest keyword first, so each span of text counts once. (D-008) |
| Multi-word keywords | Any non-letter/digit run between the words: `credit card` matches `credit-card` and `credit\ncard`. (D-024) |
| Unknown ids in a Data Set | Rejected with 422, listing them. A policy must never be silently weaker than its author thinks. (D-012) |
| Deleting a Data Type in use | Refused with 409, listing the Data Sets that use it. Also enforced by a database foreign key (`ON DELETE RESTRICT`). (D-013, D-015) |
| Scanning an unknown Data Set | 422, never `"not matched"`: reporting "clean" for a scan that didn't run would be the most dangerous answer. (D-017) |
| Input rules | `threshold` is an integer ≥ 1. Keywords are trimmed, de-duplicated and never blank. Names are unique. Lists and text have size limits. Unknown fields are rejected, with no silent type coercion. (D-009, D-010, D-011, D-018, D-035) |

Most core rules are also enforced by the database itself (unique names, `threshold ≥ 1`, known `type`, and valid links through foreign keys), so they hold even for writes that bypass the API. The remaining input rules, such as a non-empty keyword list, are enforced by request validation only.

## Architecture

```
app/
  main.py            # wiring: routers, error handlers, /health
  config.py          # settings from environment variables
  db.py              # engine, per-request session, shared save helper
  errors.py          # error catalog, code → status map, RFC 9457 rendering
  common/fields.py   # every input rule, shared by all schemas
  modules/
    datatypes/       # router · service · repository · models · schemas
    datasets/        # router · service · repository · models · schemas
    scan/            # router · service · schemas · matcher (pure, no DB/HTTP)
migrations/          # Alembic, applied on container start
tests/               # pytest: unit, repository, service and HTTP tests
postman/             # runnable Postman collection
docs/                # assignment spec and decision log
```

Every endpoint flows **router → service → repository**:
- **Routers** handle HTTP only.
- **Services** hold the business rules and raise domain errors that never mention HTTP. A single handler maps their codes to statuses.
- **Repositories** are the only code that talks to the database.

The keyword matcher is a pure module, so the core logic is tested in isolation.

## Known limitations and next steps

- **Evasion.** Whole-word keyword matching, as the spec requires, can be bypassed by gluing words together (`thesalariesleak`), inflections (`salaries` vs `salary`), leetspeak, zero-width characters or look-alike letters. The answer is layered detection, not a looser matcher:
  - text normalization (Unicode NFKC, removing invisible characters)
  - additional Data Type kinds: `regex`, and ML/LLM classifiers that judge meaning rather than exact words (self-hosted when content is sensitive)

  The `type` field and its database check are ready for new kinds.
- **No authentication or tenancy.** Every client can manage every rule.
- **Updates are full replacements (PUT).** `PATCH` would let clients send only what changes.
- **Request size.** The app caps scan text at 100,000 characters and a Data Set at 20 Data Types (422). In production, a gateway in front of the service should also cap request bodies (413), so oversized requests are refused before the app reads them.
- **No scan history or audit log.**
- **Migrations run when the API container starts.** With several replicas, they should run as a separate deploy step.
