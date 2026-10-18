FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Dependencies before code, so code edits don't invalidate the cached install layer.
COPY pyproject.toml uv.lock .python-version ./
# Includes dev dependencies so the test suite runs in this container (D-030).
RUN uv sync --frozen
COPY . .

RUN useradd --create-home app
USER app

EXPOSE 8000
# exec: uvicorn replaces the shell, so it receives Docker's stop signal and shuts down cleanly.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
