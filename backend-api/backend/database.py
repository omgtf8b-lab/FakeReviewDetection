from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings


_db_url = settings.database_url
if _db_url.startswith("sqlite:///."):
    _backend_dir = Path(__file__).resolve().parent
    _rel_path = _db_url.replace("sqlite:///.", "").lstrip("/\\")
    _abs_path = (_backend_dir / _rel_path).resolve().as_posix()
    _db_url = f"sqlite:///{_abs_path}"

connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}
engine = create_engine(_db_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
