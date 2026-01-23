import logging

from pathlib import Path
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .models import Base
from ..logging import fmt_msg

logger = logging.getLogger("inference_pipeline.api.app")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=None)


def init_database(db_url: str):
    """
    Initialize the database connection and create tables

    Parameters
    ----------
    db_url : str
        The database URL (e.g. sqlite:///software_attestations.db)

    Returns
    -------
    engine
        SQLAlchemy database engine
    """
    # Create directory for SQLite file if it doesn't exist
    if db_url.startswith("sqlite:///"):
        db_path = db_url.split("///")[1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Create database engine
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)

    logger.info(fmt_msg("✓: Internal database initialized", level=1))

    return engine


def create_session_factory(engine):
    """
    Create a session factory for the database

    Parameters
    ----------
    engine
        SQLAlchemy database engine

    Returns
    -------
    A scoped session factory
    """
    SessionLocal.configure(bind=engine)


@contextmanager
def get_session():
    """
    Create a context manager for a session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
