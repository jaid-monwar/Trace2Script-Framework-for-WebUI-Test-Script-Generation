import logging
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from src.api.config import DATABASE_URL

from src.api.models.user import User
from src.api.models.task import Task
from src.api.models.result import Result

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)


def create_db_and_tables() -> None:
    logger.info("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully.")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()