# Logging

Patient Zero logs to stdout for development. Setting `P0_LOG_DIR` also writes JSON logs to disk. Each call to `configure_logging()` starts a new log file with a unique run ID; separate ETL processes use separate files.

## Usage

Configure logging once at the entry point. Services and helpers only retrieve a logger.

```python
from p0.loggers.logger import configure_logging, get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    configure_logging()
    logger.info("Starting ETL")
```

## Output

| Level | Terminal color | Typical use |
| --- | --- | --- |
| DEBUG | Cyan | Detailed diagnostics |
| INFO | Green | Progress and run summaries |
| WARNING | Yellow | Unexpected conditions that allow processing to continue |
| ERROR | Red | Failed operations |
| CRITICAL | White on red | Failures preventing the application from continuing |

Colors appear only when stdout is an interactive terminal. Redirected output is plain text. Setting `NO_COLOR` disables colors. Colorama supports terminal colors on Windows as well as Linux.

## Configuration

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `P0_LOG_LEVEL` | `INFO` | Minimum stdout severity |
| `P0_LOG_DIR` | Unset | Enable JSON files in this directory |
| `P0_FILE_LOG_LEVEL` | `DEBUG` | Minimum file severity |
| `NO_COLOR` | Unset | Disable terminal colors when present |

These are process environment variables; logging does not load `.env`.

Example with persistent logging:

```bash
P0_LOG_DIR=logs uv run python -m etls.etl_synthea_patients --url "<download-url>" --destination data/raw/synthea/sample_latest
```

Explicit Python arguments override the environment:

```python
from pathlib import Path

log_path = configure_logging("INFO", log_dir=Path("logs"), file_level="DEBUG")
```

JSON records include a UTC timestamp, severity, logger name, filename, line number, message, and run ID. Exception logs include tracebacks. Files use the name `patient_zero_<timestamp>_<run_id>.log`; `*.log` is excluded from Git.

Deployment log directories must reside on persistent storage to survive container replacement. Files are not automatically deleted; retention is managed by the deployment. This setup expects each ETL process to configure its own logging, rather than fork workers that share an existing file handler.

## Messages and Context

Use parameterized messages and structured fields:

```python
logger.info(
    "Loaded %s patient records",
    row_count,
    extra={"dataset": "sample_latest", "stage": "raw_load", "row_count": row_count},
)
```

Extra fields appear in JSON. Console output contains the formatted message. Do not log passwords, access tokens, or patient record payloads.

Inside an exception handler, `logger.exception("Load failed")` includes the traceback. Log a failure where it is handled; lower-level functions can let exceptions reach the ETL.

## Lifecycle

`get_logger(__name__)` does not create handlers or files. Python provides the named logger hierarchy.

`configure_logging()` owns the root configuration: repeated calls replace and close existing root handlers. Call it once in a standalone entry point, not inside services or tasks running under a framework that owns logging.
