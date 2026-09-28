"""
Connect to PostgreSQL with SQLAlchemy.
"""

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import URL, Connection, Engine, create_engine

from p0.loggers.logger import get_logger


class PostgresConnector:
    """
    PostgreSQL connector.
    """

    def __init__(self) -> None:
        """
        Initialize the PostgreSQL connector.
        """
        self.logger = get_logger("PostgresConnector")
        self._engine: Engine | None = None

    def get_engine(self) -> Engine:
        """
        Create the database engine when needed and reuse it.
        """
        if self._engine is None:
            env_file = Path(__file__).resolve().parents[2] / ".env"
            settings = {**dotenv_values(env_file, interpolate=False), **os.environ}
            password = settings.get("POSTGRES_PASSWORD")
            if not password:
                raise ValueError("Set POSTGRES_PASSWORD in the environment or project .env file.")
            url = URL.create(
                "postgresql+psycopg",
                username=settings.get("POSTGRES_USER", "patient_zero"),
                password=password,
                host=settings.get("POSTGRES_HOST", "127.0.0.1"),
                port=int(settings.get("POSTGRES_PORT") or "5433"),
                database=settings.get("POSTGRES_DB", "patient_zero"),
            )
            self._engine = create_engine(
                url,
                pool_pre_ping=True,
                hide_parameters=True,
                connect_args={"connect_timeout": 10, "application_name": "patient_zero"},
            )
        return self._engine

    def connect(self) -> Connection:
        """
        Get a database connection from the engine.
        """
        self.logger.debug("Opening PostgreSQL connection")
        connection = self.get_engine().connect()
        self.logger.debug("PostgreSQL connection established")
        return connection

    def dispose(self) -> None:
        """
        Close pooled connections when the connector is no longer needed.
        """
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
