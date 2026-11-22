from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import JSON, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

# JSONB on PostgreSQL, plain JSON elsewhere (tests run on in-memory SQLite).
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


def _make_engine(url: str):
    if url.startswith("sqlite"):
        args = {"check_same_thread": False}
        if ":memory:" in url or url in ("sqlite://", "sqlite:///"):
            # One shared connection so an in-memory database survives across sessions.
            return create_engine(url, connect_args=args, poolclass=StaticPool)
        # A file database gets a connection per session: a single shared connection breaks as soon
        # as the page fires several requests at once ("bad parameter or other API misuse").
        return create_engine(url, connect_args={**args, "timeout": 30})
    return create_engine(url, pool_pre_ping=True)


engine = _make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Use in endpoints as `db: DbSession` (FastAPI's recommended Annotated style).
DbSession = Annotated[Session, Depends(get_db)]


def init_db() -> None:
    """Create all tables. Hackathon choice: no migrations, schema follows the models."""
    import app.models  # noqa: F401  (registers models on Base.metadata)

    Base.metadata.create_all(bind=engine)
    _add_missing_columns()


def _add_missing_columns() -> None:
    """create_all never alters tables: add columns introduced after the database was made."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                kind = column.type.compile(dialect=engine.dialect)
                default = " DEFAULT ''" if kind.upper() in ("TEXT", "VARCHAR") else ""
                sql = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {kind}{default}'
                conn.execute(text(sql))
