"""
Download Synthea files and load raw data.
Save each file with its download details.
"""

import csv
import gzip
import hashlib
import json
import re
import stat
import tarfile
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import IO
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen
from zipfile import ZipFile, is_zipfile

from sqlalchemy import BigInteger, Connection, LargeBinary, Text

from p0.loggers.logger import get_logger
from p0.services.DatabaseService import DatabaseService


class SyntheaService:
    """
    Synthea data service.
    """

    MAX_EXTRACTED_BYTES = 10 * 1024**3

    def __init__(self, database_service: DatabaseService | None = None) -> None:
        """
        Initialize the Synthea service.
        """
        self.logger = get_logger("SyntheaService")
        self.database_service = database_service

    def pull_data(self, url: str, destination: Path) -> tuple[Path, str]:
        """
        Download the file and return its saved path and detected type.
        Remove temporary files if any step fails.
        """
        destination.mkdir(parents=True, exist_ok=True)
        self.logger.info("Downloading Synthea file")

        with TemporaryDirectory(dir=destination) as staging:
            download_path = Path(staging) / "source.download"
            resolved_url = self.download_synthea_file(url, download_path)
            download_path, file_type = self.resolve_file_type(download_path)
            self.write_download_metadata(url, resolved_url, download_path)

            run_directory = destination / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            Path(staging).rename(run_directory)

        saved_file = run_directory / download_path.name
        self.logger.info("Saved download to %s", saved_file)
        return saved_file, file_type

    def download_synthea_file(self, url: str, path: Path) -> str:
        """
        Download the file and return its final URL after any redirects.
        """
        self.logger.info("Downloading Synthea file")
        with urlopen(url, timeout=60) as response:
            self.save_file_locally(response, path)
            return response.geturl()

    def save_file_locally(self, source: IO[bytes] | gzip.GzipFile, path: Path, max_bytes: int | None = None) -> None:
        """
        Save the file in chunks so it does not all need to fit in memory.
        """
        self.logger.debug("Writing file to %s", path)
        size = 0
        with path.open("xb") as output:
            while chunk := source.read(1024 * 1024):
                size += len(chunk)
                if max_bytes is not None and size > max_bytes:
                    raise ValueError("Extracted data exceeds the size limit.")
                output.write(chunk)
        self.logger.debug("Saved %s bytes", path.stat().st_size)

    def resolve_file_type(self, path: Path) -> tuple[Path, str]:
        """
        Identify archives and data files from their contents.
        Keep unrecognized files as text or binary data.
        """
        self.logger.debug("Checking file type for %s", path.name)
        with path.open("rb") as source:
            signature = source.read(132)

        if is_zipfile(path):
            file_type = "zip"
        elif tarfile.is_tarfile(path):
            file_type = "tar"
        elif signature.startswith(b"\x1f\x8b"):
            file_type = "gzip"
        elif signature[128:132] == b"DICM":
            file_type = "dicom"
        else:
            try:
                with path.open(encoding="utf-8-sig", newline="") as source:
                    sample = source.read(8192)
                if "\x00" in sample:
                    raise UnicodeError("Binary content")
            except UnicodeError:
                file_type = "binary"
            else:
                stripped = sample.lstrip()
                if stripped.startswith(("{", "[")):
                    file_type = "json"
                elif stripped.startswith("<"):
                    file_type = "xml"
                elif path.suffix.lower() == ".csv":
                    file_type = "csv"
                else:
                    try:
                        csv.Sniffer().sniff(sample, delimiters=",")
                        header = next(csv.reader(sample.splitlines()))
                        if any(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name) is None for name in header):
                            raise csv.Error("Not a CSV header")
                    except (csv.Error, StopIteration):
                        file_type = "text" if sample else "binary"
                    else:
                        file_type = "csv"

        self.logger.debug("Detected file type: %s", file_type)
        return path, file_type

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

    def run_etl(self, url: str, destination: Path, dataset: str) -> dict[str, int]:
        """
        Download Synthea data and load its raw tables.
        """
        self.validate_dataset_name(dataset)
        path, file_type = self.pull_data(url, destination)
        return self.load_raw_data(path, file_type, dataset)

    def validate_dataset_name(self, dataset: str) -> None:
        """
        Check the dataset name before using it in table names.
        """
        if re.fullmatch(r"[a-z][a-z0-9_]{0,29}", dataset) is None:
            raise ValueError("Dataset must start with a lowercase letter and use at most 30 lowercase letters, numbers, or underscores.")

    def extract_file(self, path: Path, file_type: str, destination: Path) -> list[Path]:
        """
        Unpack downloads and keep all regular files.
        """
        self.logger.info("Unpacking %s", path.name)
        destination.mkdir(parents=True, exist_ok=True)
        if file_type == "zip":
            self.extract_zip(path, destination)
        elif file_type == "tar":
            self.extract_tar(path, destination)
        else:
            name = path.name
            if path.name == "source.download":
                metadata = json.loads(path.with_name("metadata.json").read_text(encoding="utf-8"))
                name = Path(unquote(urlsplit(metadata["resolved_url"]).path)).name or "download"
            if file_type == "gzip" and name.lower().endswith(".gz"):
                name = name[:-3] or "download"
            target = self.extracted_file_path(name, destination)
            opener = gzip.open if file_type == "gzip" else open
            with opener(path, "rb") as source:
                self.save_file_locally(source, target, self.MAX_EXTRACTED_BYTES)
        files = sorted(file for file in destination.rglob("*") if file.is_file())
        if not files:
            raise ValueError("The download contains no files.")
        return files

    def extract_zip(self, path: Path, destination: Path) -> None:
        """
        Extract every regular file from a ZIP without following links.
        """
        remaining = self.MAX_EXTRACTED_BYTES
        with ZipFile(path) as archive:
            if len(archive.infolist()) > 100_000:
                raise ValueError("Archive contains too many files.")
            for member in archive.infolist():
                if member.is_dir():
                    continue
                mode = stat.S_IFMT(member.external_attr >> 16)
                if mode not in (0, stat.S_IFREG):
                    raise ValueError("Archive links and special files are not allowed.")
                target = self.extracted_file_path(member.filename, destination)
                with archive.open(member) as source:
                    self.save_file_locally(source, target, remaining)
                remaining -= target.stat().st_size

    def extract_tar(self, path: Path, destination: Path) -> None:
        """
        Extract every regular file from a TAR without following links.
        """
        remaining = self.MAX_EXTRACTED_BYTES
        with tarfile.open(path, "r|*") as archive:
            for index, member in enumerate(archive, start=1):
                if index > 100_000:
                    raise ValueError("Archive contains too many files.")
                if member.isdir():
                    continue
                if not member.isfile():
                    raise ValueError("Archive links and special files are not allowed.")
                target = self.extracted_file_path(member.name, destination)
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError(f"Cannot read archive file: {member.name}")
                with source:
                    self.save_file_locally(source, target, remaining)
                remaining -= target.stat().st_size

    def extracted_file_path(self, name: str, destination: Path) -> Path:
        """
        Keep the original folder path without allowing files outside the destination.
        """
        member = PurePosixPath(name)
        if member.is_absolute() or ".." in member.parts or "\\" in name or ":" in name or not member.name:
            raise ValueError(f"Unsafe archive path: {name}")
        target = destination / member
        if target.exists():
            raise ValueError(f"Duplicate file path: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def load_raw_data(self, path: Path, file_type: str, dataset: str) -> dict[str, int]:
        """
        Load every file and check the saved row counts.
        Keep the previous data if any part of the load fails.
        """
        self.validate_dataset_name(dataset)
        if self.database_service is None:
            raise RuntimeError("A database service is required to load data.")
        ds = self.database_service
        counts = {}
        with TemporaryDirectory(dir=path.parent, prefix="extracted_") as folder:
            root = Path(folder)
            files = self.extract_file(path, file_type, root)
            csv_groups: dict[str, list[Path]] = {}
            raw_files = []
            for file in files:
                _, detected_type = self.resolve_file_type(file)
                if detected_type == "csv":
                    table = f"{dataset}_{file.stem.lower()}_raw"
                    if re.fullmatch(r"[a-z][a-z0-9_]*", table) is None or len(table) > 63:
                        raise ValueError(f"Invalid table name: {table}")
                    csv_groups.setdefault(table, []).append(file)
                else:
                    raw_files.append((file, detected_type))
            table_names = set(csv_groups)
            if raw_files:
                if f"{dataset}_files_raw" in table_names:
                    raise ValueError("The CSV filename files.csv conflicts with the raw file table.")
                table_names.add(f"{dataset}_files_raw")
            with ds.transaction() as connection:
                ds.lock_load(f"synthea_data.{dataset}", connection=connection)
                ds.create_schema("synthea_data", connection=connection)
                previous_tables = {
                    name for name in ds.list_tables("synthea_data", connection=connection) if name.startswith(f"{dataset}_") and name.endswith("_raw")
                }
                if missing := previous_tables - table_names:
                    raise ValueError(f"Download is missing previously loaded tables: {', '.join(sorted(missing))}")
                for table, paths in csv_groups.items():
                    counts[table] = self.load_csv_files(paths, table, connection)
                if raw_files:
                    table = f"{dataset}_files_raw"
                    counts[table] = self.load_files(raw_files, root, table, connection)
        self.logger.info("Saved %s files into %s raw tables for %s", len(files), len(counts), dataset)
        return counts

    def load_csv_files(self, files: list[Path], table: str, connection: Connection) -> int:
        """
        Load matching CSV files into one all-text table.
        """
        if self.database_service is None:
            raise RuntimeError("A database service is required to load data.")
        ds = self.database_service
        row_count = 0
        for index, file in enumerate(files):
            with file.open(encoding="utf-8-sig", newline="") as source:
                reader = csv.reader(source, strict=True)
                columns = next(reader, [])
                if not columns or len(set(columns)) != len(columns):
                    raise ValueError(f"Missing or duplicate columns in {file.name}")
                if any(not column or len(column.encode("utf-8")) > 63 or "\x00" in column for column in columns):
                    raise ValueError(f"Invalid column name in {file.name}")
                column_types = {column: Text() for column in columns}
                if index == 0:
                    ds.create_table("synthea_data", table, column_types, connection=connection)
                ds.check_table_columns("synthea_data", table, column_types, connection=connection)
                if index == 0:
                    ds.clear_table("synthea_data", table, connection=connection)
                row_count += ds.insert_rows("synthea_data", table, columns, reader, connection=connection)
        ds.check_row_count("synthea_data", table, row_count, connection=connection)
        return row_count

    def load_files(self, files: list[tuple[Path, str]], root: Path, table: str, connection: Connection) -> int:
        """
        Save other files as original bytes with their paths and checksums.
        Split large files into chunks to keep memory use small.
        """
        if self.database_service is None:
            raise RuntimeError("A database service is required to load data.")
        ds = self.database_service
        columns = {
            "source_file": Text(),
            "file_type": Text(),
            "sha256": Text(),
            "file_size": BigInteger(),
            "chunk_index": BigInteger(),
            "content": LargeBinary(),
        }
        ds.create_table("synthea_data", table, columns, connection=connection)
        ds.check_table_columns("synthea_data", table, columns, connection=connection)
        ds.clear_table("synthea_data", table, connection=connection)
        rows = self.read_file_chunks(files, root)
        count = ds.insert_rows("synthea_data", table, list(columns), rows, batch_size=8, connection=connection)
        ds.check_row_count("synthea_data", table, count, connection=connection)
        return count

    def read_file_chunks(self, files: list[tuple[Path, str]], root: Path) -> Generator[tuple[str, str, str, int, int, bytes]]:
        """
        Read each file as numbered chunks, keeping its original bytes.
        """
        for path, file_type in files:
            with path.open("rb") as source:
                checksum = hashlib.file_digest(source, "sha256").hexdigest()
                source.seek(0)
                chunk_index = 0
                chunk = source.read(1024 * 1024)
                while chunk or chunk_index == 0:
                    yield (path.relative_to(root).as_posix(), file_type, checksum, path.stat().st_size, chunk_index, chunk)
                    chunk_index += 1
                    chunk = source.read(1024 * 1024)
