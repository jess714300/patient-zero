"""
Download and check Synthea ZIP files.
Save each file with its download details.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import BinaryIO
from urllib.request import urlopen
from zipfile import ZipFile

from p0.loggers.logger import get_logger


class SyntheaService:
    """
    Download, check, and save Synthea files.
    """

    def __init__(self) -> None:
        """
        Set up the Synthea logger.
        """
        self.logger = get_logger("SyntheaService")

    def pull_data(self, url: str, destination: Path) -> Path:
        """
        Download and check the ZIP, then save it with its download details in a new folder.
        Remove temporary files if any step fails.
        """
        destination.mkdir(parents=True, exist_ok=True)
        self.logger.info("Downloading Synthea CSV ZIP file")

        with TemporaryDirectory(dir=destination) as staging:
            archive_path = Path(staging) / "synthea.zip"
            resolved_url = self.download_synthea_file(url, archive_path)
            self.validate_archive(archive_path)
            self.write_download_metadata(url, resolved_url, archive_path)

            run_directory = destination / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            Path(staging).rename(run_directory)

        saved_archive = run_directory / "synthea.zip"
        self.logger.info("Saved validated archive to %s", saved_archive)
        return saved_archive

    def download_synthea_file(self, url: str, path: Path) -> str:
        """
        Download the file and return its final URL after any redirects.
        """
        self.logger.info("Downloading Synthea archive")
        with urlopen(url, timeout=60) as response:
            self.save_file_locally(response, path)
            return response.geturl()

    def save_file_locally(self, source: BinaryIO, path: Path) -> None:
        """
        Save the file in chunks so it does not all need to fit in memory.
        """
        self.logger.debug("Writing archive to %s", path)
        with path.open("wb") as output:
            while chunk := source.read(1024 * 1024):
                output.write(chunk)
        self.logger.info("Downloaded %s bytes", path.stat().st_size)

    def validate_archive(self, path: Path) -> None:
        """
        Check that the ZIP is readable, is not corrupt, and contains patients.csv.
        """
        self.logger.info("Validating Synthea archive")
        with ZipFile(path) as archive:
            archive.getinfo("patients.csv")
            if archive.testzip() is not None:
                raise ValueError("Synthea ZIP failed its integrity check")
        self.logger.info("Archive validation passed")

    def write_download_metadata(self, url: str, resolved_url: str, path: Path) -> None:
        """
        Save the download URLs, time, and a checksum for detecting file changes in metadata.json.
        """
        self.logger.debug("Writing download metadata")
        with path.open("rb") as source:
            checksum = hashlib.file_digest(source, "sha256").hexdigest()
        metadata = {
            "source_url": url,
            "resolved_url": resolved_url,
            "downloaded_at": datetime.now(UTC).isoformat(),
            "sha256": checksum,
        }
        path.with_name("metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
