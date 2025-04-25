# src/tools/database_connector.py

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseConnector:
    """Инструмент для подключения к базе данных"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.db_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        self._conn = None

    @contextmanager
    def get_connection(self):
        """Получение соединения с БД"""
        try:
            if self._conn is None:
                self._conn = psycopg2.connect(**self.db_params)
            yield self._conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if self._conn:
                self._conn.close()
                self._conn = None

    @contextmanager
    def get_cursor(self):
        """Получение курсора"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database query error: {e}")
                raise
            finally:
                cursor.close()