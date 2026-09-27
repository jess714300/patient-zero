"""
Create services when needed and reuse them.
"""

from p0.infrastructure.PostgresConnector import PostgresConnector
from p0.services import DatabaseService, SyntheaService


class ServiceFactory:
    """
    Create services with the connections and tools they need.
    """

    def __init__(self) -> None:
        """
        Leave services unset until they are needed.
        """
        self._synthea_service: SyntheaService | None = None
        self._database_service: DatabaseService | None = None

    @property
    def database_service(self) -> DatabaseService:
        """
        Create the database service once and reuse it.
        """
        if self._database_service is None:
            self._database_service = DatabaseService(PostgresConnector())
        return self._database_service

    @property
    def synthea_service(self) -> SyntheaService:
        """
        Create the Synthea service once and reuse it.
        """
        if self._synthea_service is None:
            self._synthea_service = SyntheaService()
        return self._synthea_service


service_factory = ServiceFactory()
