# Design Decisions

A log of design decisions, oldest first. Each entry records the context, the options considered, the decision, and why.

---

## D-001 · Language and framework: Python + FastAPI

*2026-10-16*

- **Context:** The assignment allows any language. The decision affects how easily the code can be explained and extended later.
- **Options:** Python + FastAPI · TypeScript + NestJS.
- **Decision:** Python + FastAPI.
- **Why:** Python is the developer's strongest language. FastAPI provides request validation (Pydantic) and OpenAPI generation out of the box, which covers "basic input validation" and API documentation without extra code.

## D-002 · Database: PostgreSQL

*2026-10-16*

- **Context:** The spec requires a single database. Data Sets reference Data Types by id.
- **Options:** PostgreSQL · MongoDB.
- **Decision:** PostgreSQL.
- **Why:** The Data Set → Data Type reference is relational. A relational database can enforce referential integrity itself instead of leaving it to application code.

## D-003 · Scope: standalone backend first

*2026-10-16*

- **Context:** The spec describes a backend only. The role is full-stack.
- **Options:** Backend only · backend first, then a frontend if worthwhile · both in parallel.
- **Decision:** Build a complete, standalone backend first. Then estimate the cost of a small frontend and decide.
- **Why:** The required deliverables come first. A backend with a clean, documented contract can be paired with a frontend later without changes.

## D-004 · API contract: OpenAPI generated from Pydantic

*2026-10-16*

- **Context:** A possible future frontend needs a shared contract with the backend.
- **Options:** A hand-written shared types package · OpenAPI generated from the Pydantic schemas.
- **Decision:** OpenAPI generated from the Pydantic schemas (`/openapi.json`).
- **Why:** There is a single source of truth that can't drift from the code. A TypeScript client can generate its types from it (for example with `openapi-typescript`). If no frontend is built, it still serves as the API documentation and as the basis for the Postman collection.

## D-005 · Keyword case sensitivity: per Data Type, default insensitive

*2026-10-16*

- **Context:** The spec doesn't say whether `falcon` matches `Falcon`. Case-sensitive matching is trivially bypassed by changing capitals. Case-insensitive matching causes false positives for acronyms (`IT` vs `it`).
- **Options:** Always insensitive · always sensitive · a per-Data-Type `case_sensitive` flag.
- **Decision:** An optional `case_sensitive` boolean on Data Types, defaulting to `false` (insensitive).
- **Why:** The safe default resists bypass, and acronym-heavy Data Types can opt in to exact matching. The field is optional, so requests written exactly to the spec's model still work unchanged.

## D-006 · Keyword count: every occurrence

*2026-10-16*

- **Context:** "Match if keyword count ≥ threshold" could count every occurrence or only distinct keywords. Example: keywords `[salary, bonus]`, threshold 2, text `salary salary salary` gives 3 or 1.
- **Options:** Every occurrence · distinct keywords.
- **Decision:** Every occurrence. `match_count` is the total number of keyword hits.
- **Why:** This is the standard DLP "instance count", and it reflects the volume of sensitive content. It's also the most literal reading of "keyword count". Known trade-off: one keyword repeated often (for example in a footer) can reach the threshold by itself.

## D-007 · Whole-word boundaries: letters and digits only

*2026-10-16*

- **Context:** "Whole-word keyword matching" doesn't define a word boundary. Regex `\b` treats `_` as part of a word, so it misses `salary_2024.xlsx` and `customer_salary`. Splitting on spaces misses `salary,` and `salary-related`.
- **Options:** Regex `\b` · split on whitespace · a custom boundary where only letters and digits form words.
- **Decision:** A keyword matches when the characters immediately before and after it are not letters or digits: `(?<![^\W_])keyword(?![^\W_])`.
- **Why:** It catches file names and identifiers, common places for leaks, while still rejecting `salaryman` and `salary2024`. It's the same size as the `\b` version.

## D-008 · Overlapping keywords: one hit per span of text

*2026-10-16*

- **Context:** With keywords `[credit, credit card]`, the text `credit card` could count as 2 hits (each keyword counted separately) or 1.
- **Options:** Count each keyword independently · a single search where each span of text counts once.
- **Decision:** One regex per Data Type, an alternation of all its keywords sorted longest-first (`(?:credit card|credit)`), wrapped in the D-007 boundaries. `match_count` is the number of non-overlapping matches.
- **Why:** A single mention shouldn't inflate the count. The threshold measures pieces of sensitive text, not keyword-list overlap. It also scans the text once per Data Type instead of once per keyword.

## D-009 · Threshold: required integer ≥ 1

*2026-10-16*

- **Context:** The spec types `threshold` as NUMBER. Fractions are meaningless for hit counts, and `0` would make a Data Type fire on every text, including empty text.
- **Options:** Integer ≥ 1, required · integer ≥ 1, default 1 · integer ≥ 0.
- **Decision:** Required integer, minimum 1. Other values are rejected with 422. The maximum is the longest scannable text (`MAX_SCAN_CHARS`, D-018): every hit uses at least one character, so a higher threshold could never be reached.
- **Why:** A rule's sensitivity should be a deliberate choice, not a silent default, and an always-firing rule is a configuration error.

## D-010 · Keyword list validation: normalize harmless input, reject meaningless input

*2026-10-16*

- **Context:** The spec types `content` as a string array with no constraints. An empty keyword makes the D-008 regex match empty positions, inflating `match_count` (`"Hi, the salary is attached."` gives 3 hits instead of 1).
- **Options:** Normalize harmless input and reject meaningless input · reject all irregular input · reject only empty or blank keywords.
- **Decision:** `content` must contain at least one keyword. Each keyword is trimmed. Blank keywords are rejected with 422. Exact duplicates are removed, keeping the original order.
- **Why:** Trimming and de-duplication can't change the client's intent. An empty list or a blank keyword has no sensible meaning and would corrupt matching.

## D-011 · Names: unique per entity, enforced by the database

*2026-10-16*

- **Context:** The spec doesn't require unique names. Scan results identify detections by `name`, and people choose rules by name, so duplicates make alerts and configuration ambiguous.
- **Options:** Unique, case-sensitive · unique, case-insensitive · not unique.
- **Decision:** Data Type names and Data Set names are each unique (exact match), enforced with a database `UNIQUE` constraint. A conflict returns 409.
- **Why:** It prevents ambiguous alerts at almost no cost. A database constraint is race-free, while an application-level "check then insert" is not.

## D-012 · Data Sets referencing unknown Data Types: reject

*2026-10-16*

- **Context:** A Data Set create or update may contain `data_type_ids` that don't exist (typos, already-deleted ids).
- **Options:** Reject the request · save it and drop unknown ids · save it as sent and skip missing ids at scan time.
- **Decision:** Reject the whole request with 422, listing the unknown ids in the error details. Nothing is saved.
- **Why:** A policy that is silently weaker than the admin believes is the most dangerous DLP failure. A mistyped id must fail loudly when it's written, not leave a rule that never runs.

## D-013 · Deleting a Data Type in use: block

*2026-10-16*

- **Context:** The spec doesn't say what happens to Data Sets when a Data Type they reference is deleted.
- **Options:** Block the delete · cascade (remove it from every Data Set) · allow it and leave a dangling id.
- **Decision:** Reject with 409, listing the ids of the Data Sets that reference it. The client must remove it from those Data Sets first.
- **Why:** The same principle as D-012: a policy must never be weakened silently. A cascade would let one delete disarm policies other people own. Enforced by the database via a foreign key with `ON DELETE RESTRICT` (see D-015).

## D-014 · Data Set id list: at least one, de-duplicated

*2026-10-16*

- **Context:** An empty `data_type_ids` makes every scan return "not matched", which reads as "clean" when nothing was checked. Duplicate ids would evaluate the same Data Type twice and list it twice in `detected_objects`.
- **Options:** Require at least one id and de-duplicate · allow empty ("draft") and de-duplicate · require at least one id and reject duplicates.
- **Decision:** `data_type_ids` must contain at least one id (otherwise 422). Duplicates are removed.
- **Why:** Consistent with D-010. Together with D-013 it guarantees that a Data Set always has at least one rule, so "scanned against nothing" cannot happen.

## D-015 · Data Set → Data Type links: a join table with foreign keys

*2026-10-16*

- **Context:** A Data Set references many Data Types, and a Data Type can belong to many Data Sets (many-to-many). The links can live in a separate table or in an array column on `datasets`.
- **Options:** Join table `dataset_data_types` with foreign keys · `UUID[]` array column on `datasets`.
- **Decision:** A join table with a composite primary key `(dataset_id, data_type_id)`. The `data_type_id` foreign key is `ON DELETE RESTRICT` and the `dataset_id` foreign key is `ON DELETE CASCADE`. The API still exposes a flat `data_type_ids` list.
- **Why:** Postgres cannot put foreign keys on array elements. With an array, D-012, D-013 and D-014 would rely on application checks alone, which race under concurrency (a delete and a link interleaving leave a dangling id) and don't cover writers outside the API. The join table makes the database the final guarantee (defense in depth), and "which Data Sets use this Data Type?" becomes an indexed lookup.

## D-016 · Keyword storage: a Postgres array column

*2026-10-16*

- **Context:** A Data Type's `content` is a list of keyword strings. Unlike Data Set links (D-015), nothing references keywords. They're always read and written together with their Data Type and never queried on their own.
- **Options:** A `TEXT[]` column on `data_types` · a separate `keywords` table.
- **Decision:** `content TEXT[] NOT NULL` on `data_types`.
- **Why:** There's no reference to protect, so a separate table would only add a join to every read. A native array is typed and queryable. Move keywords to their own table if they ever need their own attributes (for example per-keyword weights).

## D-017 · HTTP status codes follow RFC 9110

*2026-10-16*

- **Context:** Several decisions need an error status, and status codes have standard meanings that clients rely on.
- **Decision:** Status codes follow their RFC 9110 meaning:

  | Code | Meaning | Used for |
  |---|---|---|
  | 400 | The request is malformed | Unparseable JSON |
  | 404 | The target URL identifies nothing | `GET/PUT/DELETE /api/{datatypes,datasets}/{id}` with an unknown `id` |
  | 409 | Conflicts with current state | Duplicate name (D-011), deleting a Data Type in use (D-013) |
  | 422 | Well-formed, but contains invalid values | Field validation, unknown ids inside a body (D-012, scan `dataset_id`) |

- **Why:** 404 refers to the target resource (the URL), not to values in the body. An unknown id inside a body is invalid content, so 422. FastAPI already returns 422 for body validation errors. Implementation note: FastAPI also reports unparseable JSON as 422 by default, so a small handler maps that case to 400.
- **Scan with an unknown `dataset_id`:** 422, never `"not matched"`. Reporting "clean" for a scan that never ran would be the most dangerous possible answer.

## D-018 · Scan text limits: empty allowed, at most 100,000 characters

*2026-10-16*

- **Context:** The spec sets no limits on scanned text. Unbounded input lets a single request exhaust memory and CPU (denial of service).
- **Options (empty text):** Allow it · reject it. **Options (size):** A field length limit (422) · a body-size limit in the app (413) · a reverse proxy in front of the app (413) · no limit.
- **Decision:** Empty text is valid and returns `"not matched"`. `text` has `max_length=100_000` (lowered from 1,000,000 to bound scan cost), and longer text is rejected with 422.
- **Why:** For empty text, "not matched" is a truthful result: the scan ran and found nothing (unlike D-017's unknown Data Set, where nothing ran). For size, the field limit is the app's own rule. Request-body limits (413) belong to the gateway or ingress in front of the service in production, and the README documents this. A field limit alone still reads the body before rejecting it, which is why the gateway layer matters.

## D-019 · Scan response: the spec's shape exactly, strongest detection first

*2026-10-16*

- **Context:** The spec gives example responses but doesn't define extra fields, the "not matched" shape, or ordering.
- **Decision:**
  - Each detected object has exactly `id`, `name`, `match_count`. Matched keywords are **not** returned.
  - "Not matched" is exactly `{"status": "not matched"}`. `detected_objects` is present only on a match.
  - `detected_objects` is sorted by `match_count` descending, then `name` ascending.
- **Why:** Scan callers aren't necessarily admins, and returning matched keywords would disclose rule contents and help evasion. Admins can read rules through `/api/datatypes`. Matching the spec's examples exactly avoids breaking clients written against them. A deterministic order keeps results stable and testable, with the strongest signal first.

## D-020 · Updates: PUT (full replacement)

*2026-10-17*

- **Context:** "CRUD" needs an update operation. PUT (RFC 9110) replaces the whole resource. PATCH (RFC 5789) changes only the fields sent.
- **Options:** PUT only · PATCH only · both.
- **Decision:** `PUT /api/datatypes/{id}` and `PUT /api/datasets/{id}` take the same body as create and replace the whole resource. An unknown `id` returns 404, and a name conflict returns 409.
- **Why:** Create and update share one schema, so every write is validated as a complete object, with no partial-update edge cases (omitted vs `null` fields, merge logic). It's the simplest correct option for a small admin API. Large public APIs often prefer PATCH (Google AIP-134, Microsoft REST API Guidelines) so clients can send only what changes. Adding PATCH is a natural next step if partial updates are needed.
## D-021 · Input rules defined once as reusable field types

*2026-10-17*

- **Context:** Input rules (D-009, D-010, D-011, D-014, D-018, D-026) are spread across Data Type, Data Set and scan schemas, and some, like `name`, apply to more than one.
- **Options:** Reusable `Annotated` field types in one module · rules written inside each schema.
- **Decision:** All field rules live in `app/common/fields.py` as `Annotated` types (`Name`, `Description`, `Threshold`, `Keywords`, `DataTypeIds`, `ScanText`), and every schema uses them.
- **Why:** One place to read and audit every input rule. Shared rules are written once, and each rule is testable on its own.
## D-022 · Error body: RFC 9457 Problem Details

*2026-10-16*

- **Context:** Every error needs one consistent shape. FastAPI's defaults use two different shapes (`{"detail": "..."}` and `{"detail": [...]}`).
- **Options:** RFC 9457 Problem Details · a custom envelope `{"error": {code, message, details}}` (the style of Google AIP-193, Azure and Stripe) · FastAPI defaults.
- **Decision:** All errors, including validation errors, are returned as `application/problem+json` with the standard members `type` (`about:blank`), `title`, `status` and `detail`, plus extension members: `code` (a stable machine-readable error code) and error-specific data (for example `dataset_ids`, or `errors` for field validation failures).
- **Why:** RFC 9457 is the IETF Standards Track format for HTTP API errors, and generic clients and tools can recognize it by its media type. This continues D-017 (status codes follow the RFC). The industry is split, since large API providers use custom envelopes. The deciding factors were consistency with following published standards and interoperability.

## D-023 · Error classes: `AppError` subclasses with one code → status map

*2026-10-17*

- **Context:** Business logic needs to signal errors (D-011, D-012, D-013, D-017) without depending on HTTP, and each error needs a stable `code` (D-022) and an HTTP status.
- **Options:** One subclass per status code, with codes given at each raise · one subclass per specific error, with the status on the class · one subclass per specific error carrying only a code, with a single code → status map in the HTTP layer · FastAPI's `HTTPException` used directly.
- **Decision:** A base `AppError(Exception)` carrying `code`, `detail` and extension data. Each error the API can return is a one-line subclass that sets only its `code` (for example `DataTypeInUse`: `DATA_TYPE_IN_USE`). The HTTP layer owns one `STATUS_BY_CODE` map and a single exception handler that renders any `AppError` as RFC 9457.
- **Why:** The domain layer never names an HTTP status, so services stay transport-agnostic and could be reused from a CLI or worker unchanged. Every status lives in one table. Each error is defined once, so codes can't drift between raise sites, the module doubles as the API's error catalog, and tests can assert on exception types. This follows FastAPI's documented custom-exception-handler pattern.

## D-024 · Multi-word keywords: any non-letter/digit run between words

*2026-10-16*

- **Context:** The spec doesn't define whole-word matching for multi-word keywords such as `credit card`. Real text may contain double spaces, line breaks, hyphens or underscores between the words.
- **Options:** Any whitespace run · exactly the stored spacing · any run of non-letter/digit characters.
- **Decision:** The keyword is split on whitespace and its words are joined with `[\W_]+`. `credit card` matches `credit  card`, `credit\ncard`, `credit-card` and `credit_card.pdf`.
- **Why:** It's the same single rule as D-007 ("letters and digits form words, anything else separates them"), applied both at the edges of a keyword and between its words. Known trade-off: words from adjacent sentences can join (`credit. Card`), which gives a rare false positive and is acceptable under D-005's "a miss costs more than an extra alert" reasoning.

## D-025 · Evasion resistance: out of scope, documented

*2026-10-16*

- **Context:** Whole-word keyword matching is bypassable: concatenation (`thesalariesleak`), inflections (`salaries` vs `salary`), leetspeak (`s4lary`), spaced letters, zero-width characters, homoglyphs. Substring matching catches concatenation but floods with false positives (`hr` in "three", "christmas").
- **Options:** The spec's whole-word matching plus documented limitations · also strip invisible characters · a per-Data-Type substring mode.
- **Decision:** Implement exactly the spec's whole-word matching. The README's "Known limitations & next steps" section documents the bypasses and the layered roadmap: text normalization (Unicode NFKC, invisible-character removal), regex Data Types, and ML/LLM classifiers.
- **Why:** The spec scopes the task as a "simplified" DLP whose goal is backend design, correct logic and data modeling, and it mandates whole-word matching. Substring mode would contradict the spec. Evasion resistance belongs to additional detection layers, not to the keyword matcher.

## D-026 · Text fields: optional description, bounded lengths

*2026-10-16*

- **Context:** The spec lists `description: STRING` on Data Types without saying whether it's required. No text field has length bounds.
- **Options (description):** Optional, default `""` · required · optional and nullable.
- **Decision:** `description` is optional and defaults to `""`, at most 1,000 characters. `name` (Data Types and Data Sets) is required, 1–100 characters. Both are trimmed.
- **Why:** The description is human documentation that matching never reads, so requiring it adds friction for no value. `""` keeps the field a string as the spec types it, while `null` would change its type. Length bounds follow D-018: no unbounded input.

## D-027 · Layering: domain modules, router → service → repository

*2026-10-17*

- **Context:** The code needs a clear separation between HTTP, business rules and data access, at a size that fits a small service.
- **Options:** Router → orchestrator (one per endpoint) → service → repository · router → service → repository · router → service with direct session access.
- **Decision:** Code is organized by domain under `app/modules/{datatypes,datasets,scan}/`:
  - **Router:** HTTP only (parse, call the service, return the response model).
  - **Service:** business rules for its endpoints. Raises `AppError`s (D-023) and never touches the session directly. It may call another module's repository for read-only checks: the Data Set service verifies that Data Type ids exist, the Data Type service finds referencing Data Sets, and the scan service loads both.
  - **Repository:** persistence only, the only layer using SQLAlchemy.
  
  Response schemas read ORM objects directly (`from_attributes`), so there are no separate mappers. The keyword matcher is a pure module in `scan/` with no database or HTTP. Infrastructure endpoints (`/health`) live in `main.py`.
- **Why:** Three layers give each piece one reason to change, persistence stays isolated, and the matcher, the core logic, is unit-testable in isolation. A per-endpoint orchestrator layer would mostly forward calls in an API this size. Its job, composing across domains, is handled by a few explicit read-only repository calls. Add orchestrators if cross-domain flows grow (for example, writes spanning modules).
## D-028 · Database access: SQLAlchemy 2.0, synchronous

*2026-10-16*

- **Options:** SQLAlchemy 2.0 sync · SQLAlchemy 2.0 async · SQLModel.
- **Decision:** SQLAlchemy 2.0 ORM with synchronous sessions and the `psycopg` driver. Database models are kept separate from Pydantic API schemas.
- **Why:** It's the industry-standard Python ORM. Sync code is simpler to write, debug and test, and FastAPI runs sync endpoints in a thread pool. Scanning is CPU-bound (regex), so async I/O brings no benefit here. Keeping DB models and API schemas separate keeps storage and contract independent (D-004).

## D-029 · Schema migrations: Alembic, applied on startup

*2026-10-16*

- **Options:** Alembic applied automatically on container start · `create_all()` at startup · Alembic run manually.
- **Decision:** The schema is defined in versioned Alembic migrations, and the API container runs `alembic upgrade head` before starting the server.
- **Why:** The schema is versioned in git and can evolve (`create_all()` can't alter existing tables). Running it automatically keeps `docker compose up` a single step.

## D-030 · Tests: pytest against real PostgreSQL

*2026-10-16*

- **Options:** A real Postgres · SQLite in memory · testcontainers.
- **Decision:** pytest with FastAPI's `TestClient` against the Postgres service from docker-compose (a separate test database), with tables cleared between tests. Tests run inside the API container. The matcher has pure unit tests with no database.
- **Why:** Key rules are enforced by Postgres itself (foreign keys with `RESTRICT`, `UNIQUE`, `TEXT[]`: D-011, D-013, D-015, D-016), so only real Postgres can verify them. SQLite lacks arrays and differs in constraint behavior.

## D-031 · List endpoints: limit/offset pagination

*2026-10-16*

- **Context:** CRUD "read" needs list endpoints, since ids are server-generated UUIDs and clients need a way to discover them. Unbounded lists grow without limit.
- **Options:** Paginated plain array · no pagination · paginated with an `{items, total}` envelope.
- **Decision:** `GET /api/datatypes` and `GET /api/datasets` accept `limit` (default 50, max 200) and `offset` (default 0), and return a plain JSON array sorted by `name`.
- **Why:** Bounded responses (the same principle as D-018) in the simplest form. A stable sort makes pages deterministic.

## D-032 · No timestamps

*2026-10-16*

- **Options:** `created_at`/`updated_at` in the API · DB only · none.
- **Decision:** Records have only the spec's fields (plus D-005's `case_sensitive`).
- **Why:** Not required by the spec. Audit history would be a separate feature (an audit log) rather than two columns.

## D-033 · Logging: access logs only, never bodies

*2026-10-16*

- **Options:** Access logs only · plus scan results · full requests.
- **Decision:** Only request metadata is logged, through the server's access log (method, path, status); unexpected errors are logged with their stack trace. Request and response bodies are never logged.
- **Why:** Scan text is exactly the sensitive data a DLP protects. Logging it would turn the log files into a leak.

## D-034 · Table-level guarantees: app-generated ids, CHECK constraints

*2026-10-17*

- **Context:** Pydantic validates every API write, but the database can also enforce rules for writers outside the API (manual SQL, scripts, future services).
- **Options (ids):** Generated in Python (`uuid4`) · generated by Postgres. **Options (rules):** Database `CHECK` constraints in addition to Pydantic · Pydantic only · a native Postgres `ENUM` for `type`.
- **Decision:** Ids are generated in Python at insert. `data_types` has `CHECK (threshold >= 1)` and `CHECK (type IN ('keywords'))`, and `type` is stored as text. The link table lives with the datasets model and indexes `data_type_id`, so "which Data Sets use this Data Type?" (D-013) is an indexed lookup.
- **Why:** The same defense in depth as D-015: core invariants hold no matter who writes. Text plus `CHECK` makes adding a Data Type kind a one-line migration, while a native `ENUM` would need `ALTER TYPE`. Python-generated ids are known immediately and don't depend on the database.

## D-035 · Request strictness: unknown fields rejected, no type coercion, bounded lists

*2026-10-17*

- **Context:** By default Pydantic ignores unknown fields (a typo like `case_sensitve` is silently dropped), converts loose types (`"2"` → 2, `"no"` → false), and leaves list lengths unbounded.
- **Decision:** Every request schema forbids unknown fields (422). `threshold` and `case_sensitive` are strict, so wrong JSON types are rejected rather than converted. Strictness is per field, because model-wide strict mode would reject UUIDs, which JSON can only send as strings. Lists are bounded: at most 500 keywords of up to 100 characters each, and at most 20 Data Type ids per Data Set.
- **Why:** "Never fail silently": a dropped or reinterpreted setting would leave a rule behaving differently from what its author sent. Bounded lists cap the size of the per-Data-Type regex (D-008) and the cost of a single request, the same reasoning as D-018.
