import os

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlmodel import create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
engine = create_engine(DATABASE_URL, echo=False)

_MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")


def _make_alembic_cfg() -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", _MIGRATIONS_DIR)
    cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    return cfg


def init_db() -> None:
    cfg = _make_alembic_cfg()
    with engine.connect():
        inspector = inspect(engine)
        has_tables = bool(inspector.get_table_names())
        has_version = "alembic_version" in inspector.get_table_names()
        already_current = has_tables and not has_version

    if already_current:
        command.stamp(cfg, "head")
    else:
        command.upgrade(cfg, "head")
