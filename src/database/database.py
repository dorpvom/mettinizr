from configparser import ConfigParser
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

from database.database_objects import Base


class DatabaseError(Exception):
    pass


class SQLDatabase:
    def __init__(self, config: ConfigParser, database_path: Optional[str] = None):
        self.base = Base
        self.config = config
        database_path = database_path if database_path else config.get('Database', 'database_path')
        engine_url = f'sqlite:///{database_path}'
        self.engine = create_engine(engine_url, future=True)
        self._session_maker = sessionmaker(bind=self.engine, future=True)  # future=True => sqlalchemy 2.0 support
        self.ro_session = None

    def create_tables(self):
        self.base.metadata.create_all(self.engine)

    @contextmanager
    def get_read_write_session(self) -> Session:
        session = self._session_maker()
        try:
            yield session
            session.commit()
        except (SQLAlchemyError, DatabaseError):
            session.rollback()
            raise
        finally:
            session.invalidate()
