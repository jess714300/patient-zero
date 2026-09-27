import io
import json
import logging
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from colorama import Back, Fore, Style

from p0.loggers.logger import ColorFormatter, configure_logging, get_logger


@pytest.fixture(autouse=True)
def isolate_logging(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    for handler in original_handlers:
        root.removeHandler(handler)
    for name in ("P0_LOG_LEVEL", "P0_LOG_DIR", "P0_FILE_LOG_LEVEL", "NO_COLOR"):
        monkeypatch.delenv(name, raising=False)
    try:
        yield
    finally:
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            handler.close()
        for handler in original_handlers:
            root.addHandler(handler)
        root.setLevel(original_level)


def read_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_default_output_is_stdout_without_debug_or_ansi(capsys: pytest.CaptureFixture[str]) -> None:
    assert configure_logging() is None
    logger = get_logger("p0.tests.default")
    logger.debug("debug hidden")
    logger.info("patient count %s", 108)
    captured = capsys.readouterr()
    assert "patient count 108" in captured.out
    assert "debug hidden" not in captured.out
    assert "\x1b[" not in captured.out
    assert captured.err == ""


def test_file_includes_debug_context_and_traceback(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = configure_logging(log_dir=tmp_path / "nested" / "logs")
    assert path is not None
    logger = get_logger("p0.tests.file")
    logger.debug("download details", extra={"dataset": "synthea", "rows": 108})
    try:
        raise ValueError("invalid archive")
    except ValueError:
        logger.exception("download failed")
    records = read_records(path)
    assert [record["levelname"] for record in records] == ["DEBUG", "ERROR"]
    assert records[0]["dataset"] == "synthea"
    assert records[0]["rows"] == 108
    assert records[0]["filename"] == "test_logger.py"
    assert records[0]["lineno"] > 0
    assert records[0]["timestamp"]
    assert records[0]["run_id"] == records[1]["run_id"]
    assert "ValueError: invalid archive" in records[1]["exc_info"]
    assert "\x1b" not in path.read_text()
    captured = capsys.readouterr()
    assert "download details" not in captured.out
    assert "download failed" in captured.out


@pytest.mark.parametrize(
    ("severity", "color"),
    [
        (logging.DEBUG, Fore.CYAN),
        (logging.INFO, Fore.GREEN),
        (logging.WARNING, Fore.YELLOW),
        (logging.ERROR, Fore.RED),
        (logging.CRITICAL, Fore.WHITE + Back.RED),
    ],
)
def test_color_formatter_preserves_record_fields(severity: int, color: str) -> None:
    record = logging.LogRecord("p0.service", severity, __file__, 1, "rows %s", (108,), None)
    formatted = ColorFormatter("%(name)s %(levelname)s %(message)s").format(record)
    assert formatted.startswith(color)
    assert formatted.endswith(Style.RESET_ALL)
    assert "rows 108" in formatted
    assert record.name == "p0.service"
    assert record.levelname == logging.getLevelName(severity)
    assert record.msg == "rows %s"
    assert record.args == (108,)


def test_terminal_colors_do_not_reach_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = io.StringIO()
    monkeypatch.setattr(output, "isatty", lambda: True)
    monkeypatch.setattr(sys, "stdout", output)
    path = configure_logging(log_dir=tmp_path)
    assert path is not None
    get_logger("p0.tests.color").warning("check source")
    assert Fore.YELLOW in output.getvalue()
    record = read_records(path)[0]
    assert record["levelname"] == "WARNING"
    assert record["message"] == "check source"
    assert "\x1b" not in path.read_text()


def test_no_color_disables_terminal_colors(monkeypatch: pytest.MonkeyPatch) -> None:
    output = io.StringIO()
    monkeypatch.setattr(output, "isatty", lambda: True)
    monkeypatch.setattr(sys, "stdout", output)
    monkeypatch.setenv("NO_COLOR", "1")
    configure_logging()
    get_logger("p0.tests.no_color").info("plain output")
    assert "plain output" in output.getvalue()
    assert "\x1b[" not in output.getvalue()


def test_environment_settings_and_explicit_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("P0_LOG_LEVEL", "warning")
    monkeypatch.setenv("P0_LOG_DIR", str(tmp_path / "environment"))
    monkeypatch.setenv("P0_FILE_LOG_LEVEL", "error")
    path = configure_logging()
    assert path is not None and path.parent == tmp_path / "environment"
    logger = get_logger("p0.tests.settings")
    logger.info("info hidden")
    logger.warning("console only")
    logger.error("both outputs")
    assert [record["levelname"] for record in read_records(path)] == ["ERROR"]
    assert "info hidden" not in capsys.readouterr().out

    path = configure_logging("debug", log_dir=tmp_path / "explicit", file_level="info")
    assert path is not None and path.parent == tmp_path / "explicit"
    logger.debug("console debug")
    logger.info("file info")
    assert "console debug" in capsys.readouterr().out
    assert [record["message"] for record in read_records(path)] == ["file info"]


def test_reconfiguration_closes_old_file_without_duplicate_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    first_path = configure_logging(log_dir=tmp_path)
    old_file = next(handler for handler in logging.getLogger().handlers if isinstance(handler, logging.FileHandler))
    get_logger("p0.tests.repeat").info("first run")
    capsys.readouterr()
    second_path = configure_logging(log_dir=tmp_path)
    get_logger("p0.tests.repeat").info("second run")
    assert first_path is not None and second_path is not None and first_path != second_path
    assert old_file.stream is None
    assert capsys.readouterr().out.count("second run") == 1
    assert [record["message"] for record in read_records(first_path)] == ["first run"]
    assert [record["message"] for record in read_records(second_path)] == ["second run"]


@pytest.mark.parametrize("settings", [{"level": "invalid"}, {"file_level": "invalid"}])
def test_invalid_level_fails_before_creating_files(tmp_path: Path, settings: dict[str, str]) -> None:
    original_handlers = logging.getLogger().handlers[:]
    with pytest.raises(ValueError, match="Unknown logging level"):
        configure_logging(log_dir=tmp_path / "logs", **settings)
    assert not (tmp_path / "logs").exists()
    assert logging.getLogger().handlers == original_handlers
