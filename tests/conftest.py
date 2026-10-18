"""Test setup: a dedicated dlp_test database, migrated with Alembic and emptied after each test."""

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

TEST_DATABASE = "dlp_test"

# Must run before any app import: app.config reads DATABASE_URL once, at import time.
_dev_url = make_url(os.environ["DATABASE_URL"])
os.environ["DATABASE_URL"] = _dev_url.set(database=TEST_DATABASE).render_as_string(
    hide_password=False
)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _migrated_test_database() -> None:
    admin = create_engine(_dev_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        query = text("SELECT 1 FROM pg_database WHERE datname = :name")
        if connection.scalar(query, {"name": TEST_DATABASE}) is None:
            connection.execute(text(f"CREATE DATABASE {TEST_DATABASE}"))
    admin.dispose()
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(autouse=True)
def _empty_tables() -> Iterator[None]:
    yield
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE dataset_data_types, datasets, data_types"))


@pytest.fixture
def session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
