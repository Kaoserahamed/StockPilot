from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def normalize_database_url(url: str) -> str:
    """Accept common Postgres shorthands from PaaS providers.

    Render/Heroku/Supabase sometimes supply `postgres://...`; SQLAlchemy
    expects `postgresql+psycopg2://...`. MySQL and sqlite URLs pass through.
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


DATABASE_URL = normalize_database_url(settings.database_url)

connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Connection pooling configured via settings for production tuning.
_engine_kwargs: dict = {"pool_pre_ping": True, "connect_args": connect_args}
if not IS_SQLITE:
    _engine_kwargs.update(
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
        pool_timeout=30,
    )
engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def ensure_indexes() -> None:
    """Create missing indexes on existing tables (idempotent, non-destructive).

    Model changes after the tables were already created (e.g. composite query
    indexes) would otherwise never reach an existing MySQL/Postgres database.
    Only used for demos/service upgrades — migrations should use Alembic.
    """
    from app.db.base import Base
    from sqlalchemy.schema import CreateIndex

    insp = inspect(engine)
    existing = {
        (t, ix["name"])
        for t in insp.get_table_names()
        for ix in insp.get_indexes(t)
    }
    for table in Base.metadata.tables.values():
        if not insp.has_table(table.name):
            continue
        for ix in table.indexes:
            if (table.name, ix.name) in existing:
                continue
            try:
                with engine.begin() as conn:
                    conn.execute(CreateIndex(ix))
                print(f"[db] created missing index {table.name}.{ix.name}")
            except Exception as exc:  # pragma: no cover - DDL dialect differences
                print(f"[db] could not auto-create {table.name}.{ix.name}: {exc}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
