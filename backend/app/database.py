"""SQLAlchemy engine, session factory, declarative Base and DB init helper."""

from collections.abc import Generator

from sqlalchemy import Integer, create_engine, inspect
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

# SQLite needs this to be usable across threads (FastAPI runs in a threadpool).
_connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables and idempotently maintain the local demo seed.

    Imports app.models so every model is registered with Base.metadata before
    create_all runs, and imports seed lazily to avoid a circular import.
    """
    import app.models  # noqa: F401  -- registers models with Base.metadata
    from app.models import Application, DocumentCategory, User
    from app.seed import seed_demo_data

    Base.metadata.create_all(bind=engine)
    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    if "token_version" not in user_columns:
        integer_type = Integer().compile(dialect=engine.dialect)
        with engine.begin() as connection:
            connection.exec_driver_sql(
                f"ALTER TABLE users ADD COLUMN token_version {integer_type} NOT NULL DEFAULT 0"
            )
    db = SessionLocal()
    try:
        has_demo_account = db.query(User).filter_by(
            email="admin@nexora-demo.in"
        ).first() is not None
        needs_initial_seed = (
            db.query(User).count() == 0
            or db.query(Application).count() == 0
            or db.query(DocumentCategory).count() == 0
        )
        if needs_initial_seed or has_demo_account:
            seed_demo_data(db)
    finally:
        db.close()
