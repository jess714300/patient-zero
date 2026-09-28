"""
Synthea provides fictional patient data with personal details and medical histories.
These records do not describe real patients.

This ETL downloads Synthea files and loads their raw data into PostgreSQL.
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
    description="Download Synthea files and load raw data.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument(
    "-u",
    "--url",
    help="Required: Direct download URL for a Synthea file or archive.",
    required=True,
    type=str,
)

parser.add_argument(
    "-d",
    "--destination",
    help="Local folder for downloads and their details.",
    default=Path(__file__).resolve().parents[1] / "data" / "raw" / "synthea",
    type=Path,
)


parser.add_argument(
    "-n",
    "--dataset",
    help="Required: Table prefix, such as sample_latest or covid19_100k.",
    required=True,
    type=str,
)


def main() -> int:
    """
    Run the Synthea ETL and report success or failure.
    """
    configure_logging()
    cli_args = parser.parse_args()

    try:
        ss: SyntheaService = service_factory.synthea_service
        ds: DatabaseService = service_factory.database_service
        logger.info("Starting Synthea raw load")
        ds.check_connection()
        ss.run_etl(cli_args.url, cli_args.destination, cli_args.dataset)
        logger.info("Synthea raw load completed successfully")
        return 0
    except Exception:
        logger.exception("Synthea raw load failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
