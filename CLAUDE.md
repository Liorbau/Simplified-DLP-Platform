# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

A simplified DLP (Data Loss Prevention) backend. It manages keyword-based **Data Types**, groups them into **Data Sets**, and scans input text against a Data Set.

- Spec: [`docs/ASSIGNMENT.md`](docs/ASSIGNMENT.md) (the original PDF is in `docs/` and is the source of truth).
- Design decisions: [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Stack

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 (sync, psycopg) · Alembic · PostgreSQL · pytest · uv · ruff · Docker Compose.

## Layout

```
app/
  main.py            # wiring: routers, exception handlers, /health
  config.py          # settings from environment variables
  db.py              # engine + per-request session
  errors.py          # AppError family, code → status map, RFC 9457 handler
  common/fields.py   # every input rule, shared by all modules (D-021)
  modules/
    <domain>/        # datatypes, datasets, scan
      router.py          # HTTP only
      service.py         # business rules; raises AppError, never touches the session
      repository.py      # persistence only; the only layer using SQLAlchemy
      models.py          # SQLAlchemy tables
      schemas.py         # Pydantic request/response models (the API contract)
migrations/          # Alembic
tests/
```

Every business endpoint flows router → service → repository (D-027). A service may call another module's repository only for read-only checks. Response schemas read ORM objects directly (`from_attributes`). Create only the files a module needs.

## Configuration

- All settings come from environment variables. The code never contains values.
- `docker-compose.yml` supplies local-only defaults as `${VAR:-default}`, so `docker compose up` needs no setup. `.env.example` documents every variable.
- The Postgres port isn't published outside the Docker network. Tests run inside the API container.
- Never log request or response bodies (D-033).

## Deliverables

- Source code in a public Git repository
- A working `docker-compose.yml`
- A Postman collection
- A README explaining how to run the application

## Workflow

- **The developer owns the code; Claude proposes.** Every design or architecture decision, however small, is presented as a multiple-choice question with Claude's recommendation marked. The developer makes the decision.
- Architecture and design decisions that shape the code are recorded in `docs/DECISIONS.md` (context, options, decision, rationale). Tooling and housekeeping choices are not.
- Spec ambiguities are resolved by explicit decision, never silently. Each resolution is recorded and covered by a test.
- Changes land in small, reviewable chunks of about 3 files or 150 lines, then stop for review. After each non-trivial chunk, ask 1–3 questions that check the developer can explain it.
- Prefer the simplest correct solution: standard library and framework features first, no speculative abstractions.
- Verify before calling a chunk done: `ruff check`, `ruff format --check`, and the tests.

## Conventions

- **Contract:** Pydantic schemas are the API contract. Every endpoint declares its request and response models, and FastAPI publishes them at `/openapi.json`. Every route declares a response schema; ORM objects a route returns are converted through it (`from_attributes`), so internals never leak.
- **Comments:** zero by default. Names and structure explain the code. Every file opens with a one-line docstring stating its role. A comment is allowed only for a non-obvious invariant, security subtlety or workaround: one short line directly above the line it explains. Never narrate what the code says.
- **Python style:** type hints and explicit return types on every function; functions return a meaningful value; `UPPER_CASE` module constants at the top; a `_` prefix for private helpers; `is None` / `is not None` for missing values.
- **Errors:** never fail silently, and never substitute a fallback that hides a bug.
- **Tests:** one scenario per test; explicit tests for invariants (referential integrity, de-duplication) and for mutation edge cases (unknown ids). Tests run against a dedicated test database, never the dev database.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) with the area as scope: `feat(scan): …`, `fix(datatypes): …`, `docs: …`, `chore: …`. One logical concern per commit. AI-assisted commits carry a `Co-Authored-By: Claude` trailer.
