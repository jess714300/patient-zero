"""
Open PostgreSQL connections using environment variables or the project's .env file.
"""

import os
from pathlib import Path

import psycopg
from dotenv import dotenv_values

from p0.loggers.logger import get_logger


class PostgresConnector:
    """
    Open a new connection when a database operation needs one.
    """

    def __init__(self) -> None:
        """
        Set up the connector logger.
        """
        self.logger = get_logger("PostgresConnector")

    def connect(self) -> psycopg.Connection:
        """
        Connect to PostgreSQL with settings from the environment or .env.
        """
        env_file = Path(__file__).resolve().parents[2] / ".env"
        settings = {**dotenv_values(env_file, interpolate=False), **os.environ}
        password = settings.get("POSTGRES_PASSWORD")
        if not password:
            raise ValueError("Set POSTGRES_PASSWORD in the environment or project .env file.")

        self.logger.debug("Opening PostgreSQL connection")
        connection = psycopg.connect(
            host=settings.get("POSTGRES_HOST", "127.0.0.1"),
            port=settings.get("POSTGRES_PORT", "5433"),
            dbname=settings.get("POSTGRES_DB", "patient_zero"),
            user=settings.get("POSTGRES_USER", "patient_zero"),
            password=password,
            connect_timeout=10,
            application_name="patient_zero",
        )
        self.logger.debug("PostgreSQL connection established")
        return connection
