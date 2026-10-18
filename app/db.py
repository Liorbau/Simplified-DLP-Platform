"""Database engine, the ORM base class, the per-request session and the shared commit helpers."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings
from app.errors import AppError

UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"

# pool_pre_ping: a connection broken by a DB restart is replaced instead of failing a request.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def save[T](session: Session, instance: T, errors: dict[str, AppError]) -> T:
    session.add(instance)
    commit(session, errors)
    return instance


def commit(session: Session, errors: dict[str, AppError]) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        error = errors.get(getattr(exc.orig, "sqlstate", ""))
        if error is None:
            raise
        raise error from exc
