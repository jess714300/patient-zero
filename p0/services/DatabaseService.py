"""
Read and write database data with SQLAlchemy.
"""

from collections.abc import Generator, Iterable, Mapping, Sequence
from contextlib import contextmanager, nullcontext
from itertools import batched
from typing import Any

from sqlalchemy import Column, Connection, MetaData, Table, func, inspect, select, text
from sqlalchemy.schema import CreateSchema
from sqlalchemy.sql import Executable
from sqlalchemy.types import TypeEngine

from p0.infrastructure.PostgresConnector import PostgresConnector
from p0.loggers.logger import get_logger


class DatabaseService:
    """
    Database service.
    """

    def __init__(self, connector: PostgresConnector) -> None:
        """
        Initialize the database service.
        """
        self.connector = connector
        self.logger = get_logger("DatabaseService")

    @contextmanager
    def transaction(self) -> Generator[Connection]:
        """
        Save changes on success or undo them on failure.
        Pass this connection to database methods to group their changes together.
        """
        self.logger.debug("Opening database transaction")
        with self.connector.connect() as connection, connection.begin():
            yield connection
        self.logger.debug("Database transaction completed and connection released")

    def check_connection(self) -> None:
        """
        Check that the database connection works.
        """
        self.logger.info("Checking database connection")
        if self.fetch_one("SELECT 1 AS connection_check") != {"connection_check": 1}:
            raise RuntimeError("Database connection check returned an unexpected result.")
        self.logger.info("Database connection successful")

    def execute_statement(
        self,
        statement: str | Executable,
        parameters: Mapping[str, Any] | None = None,
        *,
        connection: Connection | None = None,
    ) -> int:
        """
        Run a statement and return the number of rows affected, or -1 if unknown.
        Use named parameters such as :patient_id for values.
        """
        self.logger.debug("Running database statement")
        if isinstance(statement, str):
            statement = text(statement)
        connection_context = self.transaction() if connection is None else nullcontext(connection)
        with connection_context as active_connection, active_connection.execute(statement, parameters or {}) as result:
            row_count = result.rowcount
        self.logger.debug("Database statement finished; rows affected: %s", row_count)
        return row_count

    def fetch_one(
        self,
        statement: str | Executable,
        parameters: Mapping[str, Any] | None = None,
        *,
        connection: Connection | None = None,
    ) -> dict[str, Any] | None:
        """
        Return the first result as a dictionary, or None if no rows match.
        """
        self.logger.debug("Fetching one database row")
        if isinstance(statement, str):
            statement = text(statement)
        connection_context = self.transaction() if connection is None else nullcontext(connection)
        with connection_context as active_connection, active_connection.execute(statement, parameters or {}) as result:
            row = result.mappings().first()
        self.logger.debug("Database row found: %s", row is not None)
        return dict(row) if row is not None else None

    def fetch_all(
        self,
        statement: str | Executable,
        parameters: Mapping[str, Any] | None = None,
        *,
        connection: Connection | None = None,
    ) -> list[dict[str, Any]]:
        """
        Return all results as a list of dictionaries.
        Limit the query when the full result may not fit in memory.
        """
        self.logger.debug("Fetching database rows")
        if isinstance(statement, str):
            statement = text(statement)
        connection_context = self.transaction() if connection is None else nullcontext(connection)
        with connection_context as active_connection, active_connection.execute(statement, parameters or {}) as result:
            rows = [dict(row) for row in result.mappings()]
        self.logger.debug("Fetched %s database rows", len(rows))
        return rows

    def create_schema(self, schema: str, *, connection: Connection | None = None) -> None:
        """
        Create the schema if it does not exist.
        """
        self.logger.info("Creating schema if needed: %s", schema)
        self.execute_statement(CreateSchema(schema, if_not_exists=True), connection=connection)

    def create_table(
        self,
        schema: str,
        table: str,
        columns: Mapping[str, TypeEngine],
        *,
        connection: Connection | None = None,
    ) -> None:
        """
        Create a table using column names and SQLAlchemy types.
        Leave existing tables unchanged.
        """
        if not columns:
            raise ValueError("Provide at least one column.")
        target = Table(table, MetaData(), *(Column(name, data_type) for name, data_type in columns.items()), schema=schema)
        self.logger.info("Creating table if needed: %s.%s", schema, table)
        connection_context = self.transaction() if connection is None else nullcontext(connection)
        with connection_context as active_connection:
            target.create(active_connection, checkfirst=True)

    def clear_table(self, schema: str, table: str, *, connection: Connection | None = None) -> int:
        """
        Delete all rows without dropping the table and return the number removed.
        """
        self.logger.info("Clearing table: %s.%s", schema, table)
        target = Table(table, MetaData(), schema=schema)
        return self.execute_statement(target.delete(), connection=connection)

    def insert_rows(
        self,
        schema: str,
        table: str,
        columns: Sequence[str],
        rows: Iterable[Sequence[Any]],
        *,
        connection: Connection | None = None,
        batch_size: int = 1000,
    ) -> int:
        """
        Add rows to an existing table in batches and return the number submitted.
        """
        if not columns or len(set(columns)) != len(columns):
            raise ValueError("Provide at least one column name with no duplicates.")
        if batch_size < 1:
            raise ValueError("Batch size must be at least 1.")
        target = Table(table, MetaData(), *(Column(name) for name in columns), schema=schema)
        self.logger.info("Inserting rows into %s.%s", schema, table)
        row_count = 0
        connection_context = self.transaction() if connection is None else nullcontext(connection)
        with connection_context as active_connection:
            for batch in batched(rows, batch_size, strict=False):
                records = [dict(zip(columns, row, strict=True)) for row in batch]
                with active_connection.execute(target.insert(), records):
                    row_count += len(records)
        self.logger.info("Submitted %s rows to %s.%s", row_count, schema, table)
        return row_count

    def count_rows(self, schema: str, table: str, *, connection: Connection | None = None) -> int:
        """
        Return the number of rows in the table.
        """
        target = Table(table, MetaData(), schema=schema)
        statement = select(func.count().label("row_count")).select_from(target)
        result = self.fetch_one(statement, connection=connection)
        if result is None:
            raise RuntimeError("Database did not return a row count.")
        return int(result["row_count"])

    def check_row_count(self, schema: str, table: str, expected_count: int, *, connection: Connection | None = None) -> None:
        """
        Raise an error if the table does not have the expected number of rows.
        """
        if expected_count < 0:
            raise ValueError("Expected row count cannot be negative.")
        actual_count = self.count_rows(schema, table, connection=connection)
        if actual_count != expected_count:
            raise ValueError(f"Row count mismatch for {schema}.{table}: expected {expected_count}, found {actual_count}.")
        self.logger.info("Row count passed for %s.%s: %s", schema, table, actual_count)

    def lock_load(self, name: str, *, connection: Connection) -> None:
        """
        Keep two loads with the same name from writing at the same time.
        """
        self.execute_statement(
            "SELECT pg_advisory_xact_lock(hashtextextended(:name, 0))",
            {"name": name},
            connection=connection,
        )

    def list_tables(self, schema: str, *, connection: Connection | None = None) -> list[str]:
        """
        Return the table names in a schema.
        """
        connection_context = self.transaction() if connection is None else nullcontext(connection)
        with connection_context as active_connection:
            return inspect(active_connection).get_table_names(schema=schema)

    def check_table_columns(
        self,
        schema: str,
        table: str,
        columns: Mapping[str, TypeEngine],
        *,
        connection: Connection | None = None,
    ) -> None:
        """
        Check column names and types before replacing a table's rows.
        """
        connection_context = self.transaction() if connection is None else nullcontext(connection)
        with connection_context as active_connection:
            existing = inspect(active_connection).get_columns(table, schema=schema)
            actual = [(column["name"], column["type"].compile(dialect=active_connection.dialect)) for column in existing]
            expected = [(name, data_type.compile(dialect=active_connection.dialect)) for name, data_type in columns.items()]
            if actual != expected:
                raise ValueError(f"Columns do not match {schema}.{table}. Existing rows were not replaced.")
