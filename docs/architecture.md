# Architecture

Patient Zero separates executable workflows, reusable services, and external-system access. A service factory constructs shared services and supplies their dependencies.

## Project Structure

```text
patient-zero/
|-- dags/                   # Schedules and dependencies between ETLs
|-- etls/                   # Command-line entry points and ETL step coordination
|-- p0/
|   |-- domain/             # Healthcare concepts and data definitions
|   |-- factories/
|   |   |-- ServiceFactory.py
|   |-- helpers/            # Stateless utilities, including calendar functions
|   |-- infrastructure/     # External clients, connectors, and file access
|   |-- loggers/
|   |   |-- logger.py
|   |-- services/
|       |-- DatabaseService.py
|       |-- SyntheaService.py
|-- docs/
|-- tests/
```

The factory and service modules are placeholders; logging is implemented. Configuration, custom exceptions, repositories, and observability packages are absent until they have concrete responsibilities.

## Factories and Services

### ServiceFactory

`p0/factories/ServiceFactory.py` owns service construction and dependency injection. Each service is created on first access and reused within that factory instance. The factory supplies the shared `DatabaseService` to `SyntheaService`.

Factories construct objects; they do not download data, execute ETLs, or contain SQL. A separate database factory and lazy-import component are not part of the initial structure.

### DatabaseService

`p0/services/DatabaseService.py` owns reusable PostgreSQL operations and transaction boundaries. Both raw and normalized writes use this service. Sharing a service does not require keeping one connection or transaction open for an entire ETL.

Source-specific transformations belong to the source service, not the database service. Low-level connection components can live in `p0/infrastructure/` when needed.

### SyntheaService

`p0/services/SyntheaService.py` owns Synthea-specific operations. Acquisition, archive handling, metadata recording, raw loading, normalization, and normalized loading have separate functions or methods. Database access is supplied through `DatabaseService`.

Large downloads stream to a local file rather than returning the complete archive in memory. Generic HTTP and file-access components belong in infrastructure when extracted from the source-specific code.

## ETLs and DAGs

ETLs live in the top-level `etls/` directory and use the `etl_` filename prefix. An ETL parses its arguments and coordinates service operations:

```text
Pull source data
    |
Write raw records to PostgreSQL
    |
Normalize records
    |
Write normalized records to PostgreSQL
```

Raw records remain available for inspection and normalization retries. A successful raw load is committed before normalization; failed normalized loads must not leave partially published results. Exact loading and retry contracts are defined with the table implementations.

DAGs live in `dags/`. They schedule ETLs and define dependencies between them. Argument parsing occurs under the ETL's `__main__` guard so its functions can also be imported.

## Supporting Packages

| Package | Responsibility |
| --- | --- |
| `domain` | Healthcare entities, clinical concepts, and meaningful data definitions |
| `helpers` | Reusable stateless functions such as calendar handling, type conversion, validation, and output formatting |
| `infrastructure` | External clients, database connectors, downloads, and file access |
| `loggers` | Shared logging configuration and named logger access |

Executable backfills and ETL runners belong with workflows. A helper performs a focused reusable operation rather than coordinating an application workflow.

## Logging

`configure_logging()` initializes root stdout logging once at an entry point. Modules retrieve their logger with `get_logger(__name__)`. Services and helpers do not configure logging during import.
