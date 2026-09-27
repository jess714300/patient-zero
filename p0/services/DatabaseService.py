"""
Group database operations into transactions and check the connection.
"""

from collections.abc import Generator
from contextlib import contextmanager

import psycopg

from p0.infrastructure.PostgresConnector import PostgresConnector
from p0.loggers.logger import get_logger


class DatabaseService:
    """
    Save database changes together, or undo them if an operation fails.
    """

    def __init__(self, connector: PostgresConnector) -> None:
        """
        Store the connector without opening a connection.
        """
        self.connector = connector
        self.logger = get_logger("DatabaseService")

    @contextmanager
    def transaction(self) -> Generator[psycopg.Connection]:
        """
        Save changes on success or undo them on failure, then close the connection.
        """
        self.logger.debug("Opening database connection")
        with self.connector.connect() as connection:
            yield connection
        self.logger.debug("Database transaction completed and connection closed")

    def check_connection(self) -> None:
        """
        Check that the database connection works.
        """
        self.logger.info("Checking database connection")
        with self.transaction() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                raise RuntimeError("Database connection check returned an unexpected result.")
        self.logger.info("Database connection successful")
