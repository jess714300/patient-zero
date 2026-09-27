"""
Synthea provides fictional patient data with personal details and medical histories.
These records do not describe real patients.

This ETL downloads the packaged Synthea archive, normalizes the extracted patient
records, and writes the resulting data to the configured database.
"""

import argparse
import sys
from pathlib import Path

from p0.factories.ServiceFactory import service_factory
from p0.loggers.logger import configure_logging, get_logger
from p0.services import DatabaseService, SyntheaService

# Instantiate Logger
logger = get_logger("etl_synthea_patients")

# Arg Parser
parser = argparse.ArgumentParser(
    description="Download a Synthea ZIP archive, save it locally, and ingest the synthetic patient data files it contains.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument(
    "-u",
    "--url",
    help="Required: Direct download URL for the Synthea ZIP archive or packaged data file.",
    required=True,
    type=str,
)

parser.add_argument(
    "-d",
    "--destination",
    help="Local folder for ZIP files and download details.",
    default=Path(__file__).resolve().parents[1] / "data" / "raw" / "synthea",
    type=Path,
)


def main() -> int:
    """
    Run the Synthea ETL and report success or failure.
    """
    configure_logging()
    cli_args = parser.parse_args()

    try:
        ss: SyntheaService = service_factory.synthea_service
        ds: DatabaseService = service_factory.database_service  # noqa: F841 - Database loading will use this service.
        logger.info("Starting Synthea download")
        ss.pull_data(cli_args.url, cli_args.destination)
        logger.info("Synthea download completed successfully")
        return 0
    except Exception:
        logger.exception("Synthea download failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
