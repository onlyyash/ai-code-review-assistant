from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

# Use SQLite for now; you can switch to PostgreSQL by changing the URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./submissions.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency: one session per request, always closed, even when
    the request fails."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _add_missing_columns():
    """create_all() never alters existing tables, so a database created by an
    older version would lack new columns. Add any that are missing."""
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name not in existing:
                    col_type = column.type.compile(engine.dialect)
                    conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN "{column.name}" {col_type}'))


def init_db():
    Base.metadata.create_all(bind=engine)
    _add_missing_columns()
