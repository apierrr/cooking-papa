from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401
    from sqlalchemy import inspect
    insp = inspect(engine)
    # Legacy schema (pre steps_json) uses description NOT NULL — drop it on a fresh/empty DB.
    if insp.has_table("recipes"):
        cols = {c["name"] for c in insp.get_columns("recipes")}
        if "steps_json" not in cols:
            with engine.begin() as conn:
                conn.exec_driver_sql("DROP TABLE IF EXISTS preparation_requests")
                conn.exec_driver_sql("DROP TABLE IF EXISTS recipe_ingredients")
                conn.exec_driver_sql("DROP TABLE IF EXISTS recipes")
        else:
            with engine.begin() as conn:
                if "category" not in cols:
                    conn.exec_driver_sql("ALTER TABLE recipes ADD COLUMN category VARCHAR(20)")
                if "origin" not in cols:
                    conn.exec_driver_sql("ALTER TABLE recipes ADD COLUMN origin VARCHAR(100)")
                conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_recipes_category ON recipes (category)")
                conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_recipes_origin ON recipes (origin)")
    Base.metadata.create_all(bind=engine)
