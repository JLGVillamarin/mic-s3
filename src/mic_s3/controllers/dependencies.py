from contextlib import contextmanager
from sqlalchemy.orm import Session
from mic_s3.db import get_engine


@contextmanager
def get_session():
    engine = get_engine()
    with Session(engine, expire_on_commit=False) as session:
        yield session
