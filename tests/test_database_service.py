from unittest.mock import MagicMock, patch

import pytest

from p0.factories.ServiceFactory import ServiceFactory
from p0.infrastructure.PostgresConnector import PostgresConnector
from p0.services import DatabaseService


def test_connector_uses_local_defaults() -> None:
    with (
        patch("p0.infrastructure.PostgresConnector.dotenv_values", return_value={"POSTGRES_PASSWORD": "test-only"}),
        patch.dict("os.environ", {}, clear=True),
        patch("p0.infrastructure.PostgresConnector.psycopg.connect") as connect,
    ):
        assert PostgresConnector().connect() is connect.return_value
        connect.assert_called_once_with(
            host="127.0.0.1",
            port="5433",
            dbname="patient_zero",
            user="patient_zero",
            password="test-only",
            connect_timeout=10,
            application_name="patient_zero",
        )


def test_environment_overrides_local_file() -> None:
    settings = {
        "POSTGRES_HOST": "postgres",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "test_db",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "environment-only",
    }
    with (
        patch("p0.infrastructure.PostgresConnector.dotenv_values", return_value={"POSTGRES_PASSWORD": "file-only"}),
        patch.dict("os.environ", settings, clear=True),
        patch("p0.infrastructure.PostgresConnector.psycopg.connect") as connect,
    ):
        PostgresConnector().connect()
        assert connect.call_args.kwargs["password"] == "environment-only"
        assert connect.call_args.kwargs["host"] == "postgres"
        assert connect.call_args.kwargs["port"] == "5432"
        assert connect.call_args.kwargs["dbname"] == "test_db"
        assert connect.call_args.kwargs["user"] == "test_user"


def test_missing_password_fails_before_connecting() -> None:
    with (
        patch("p0.infrastructure.PostgresConnector.dotenv_values", return_value={}),
        patch.dict("os.environ", {}, clear=True),
        patch("p0.infrastructure.PostgresConnector.psycopg.connect") as connect,
    ):
        with pytest.raises(ValueError, match="POSTGRES_PASSWORD"):
            PostgresConnector().connect()
        connect.assert_not_called()


def test_database_factory_is_lazy_and_reuses_service() -> None:
    with patch("p0.factories.ServiceFactory.PostgresConnector") as connector:
        factory = ServiceFactory()
        connector.assert_not_called()
        first = factory.database_service
        assert factory.database_service is first
        connector.assert_called_once_with()
        connector.return_value.connect.assert_not_called()


def test_transaction_uses_connection_context() -> None:
    connector = MagicMock(spec=PostgresConnector)
    service = DatabaseService(connector)
    with service.transaction() as connection:
        assert connection is connector.connect.return_value.__enter__.return_value
    connector.connect.return_value.__exit__.assert_called_once_with(None, None, None)


def test_transaction_passes_failure_to_connection_context() -> None:
    connector = MagicMock(spec=PostgresConnector)
    connector.connect.return_value.__exit__.return_value = False
    service = DatabaseService(connector)
    with pytest.raises(ValueError, match="load failed"), service.transaction():
        raise ValueError("load failed")
    assert connector.connect.return_value.__exit__.call_args.args[0] is ValueError


@pytest.mark.parametrize("result", [(1,), None])
def test_connection_check(result: tuple[int] | None) -> None:
    connector = MagicMock(spec=PostgresConnector)
    connection = connector.connect.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = result
    service = DatabaseService(connector)
    if result is None:
        with pytest.raises(RuntimeError, match="unexpected result"):
            service.check_connection()
    else:
        service.check_connection()
    cursor.execute.assert_called_once_with("SELECT 1")
