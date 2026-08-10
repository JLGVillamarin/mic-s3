from sqlalchemy import create_engine, Engine

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        import os
        db_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://s3:s3@localhost:5432/s3"
        )
        _engine = create_engine(db_url)
    return _engine


def set_engine(engine: Engine) -> None:
    """For testing: inject a custom engine."""
    global _engine
    _engine = engine
