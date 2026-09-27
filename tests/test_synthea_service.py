import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
from zipfile import BadZipFile, ZipFile

import pytest

from p0.factories.ServiceFactory import ServiceFactory
from p0.services import SyntheaService


def make_archive(path: Path, member: str = "patients.csv") -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr(member, "Id,ZIP\nexample,01535\n")


def test_factory_constructs_service_only_once() -> None:
    with patch("p0.factories.ServiceFactory.SyntheaService", wraps=SyntheaService) as constructor:
        factory = ServiceFactory()
        constructor.assert_not_called()
        first = factory.synthea_service
        assert factory.synthea_service is first
        constructor.assert_called_once_with()


def test_pull_data_preserves_archive_and_provenance(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    make_archive(source)
    destination = tmp_path / "downloads"
    saved = SyntheaService().pull_data(source.as_uri(), destination)
    assert saved.read_bytes() == source.read_bytes()
    metadata = json.loads(saved.with_name("metadata.json").read_text())
    assert metadata["source_url"] == source.as_uri()
    assert metadata["resolved_url"] == source.as_uri()
    assert metadata["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert metadata["downloaded_at"]
    assert list(destination.iterdir()) == [saved.parent]


@pytest.mark.parametrize("valid_zip", [True, False])
def test_invalid_source_is_not_published(tmp_path: Path, valid_zip: bool) -> None:
    source = tmp_path / "source.zip"
    if valid_zip:
        make_archive(source, "other.csv")
    else:
        source.write_bytes(b"not a ZIP")
    destination = tmp_path / "downloads"
    with pytest.raises((KeyError, BadZipFile)):
        SyntheaService().pull_data(source.as_uri(), destination)
    assert list(destination.iterdir()) == []


def test_download_failure_cleans_staging_directory(tmp_path: Path) -> None:
    destination = tmp_path / "downloads"
    with pytest.raises(OSError):
        SyntheaService().pull_data((tmp_path / "missing.zip").as_uri(), destination)
    assert list(destination.iterdir()) == []


def test_cli_runs_through_service_and_reports_failure(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    make_archive(source)
    command = [sys.executable, "-m", "etls.etl_synthea_patients", "-d", str(tmp_path / "downloads")]
    success = subprocess.run([*command, "-u", source.as_uri()], capture_output=True, text=True)
    assert success.returncode == 0, success.stderr
    assert "SyntheaService" in success.stdout
    assert "etl_synthea_patients" in success.stdout
    assert "completed successfully" in success.stdout
    failure = subprocess.run([*command, "-u", (tmp_path / "missing.zip").as_uri()], capture_output=True, text=True)
    assert failure.returncode == 1
    assert failure.stdout.count("Synthea download failed") == 1


def test_etl_import_does_not_parse_arguments_or_construct_service() -> None:
    script = (
        "from p0.factories.ServiceFactory import service_factory; import etls.etl_synthea_patients; assert service_factory._synthea_service is None"
    )
    result = subprocess.run([sys.executable, "-c", script, "--unrelated-dag-argument"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
