"""Alembic entry point: runs migrations against the app's database."""

from alembic import context

import app.modules.datasets.models  # noqa: F401  (registers every table on Base.metadata)
from app.db import Base, engine

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
