# Development

## Standards

Patient Zero uses a consistent development environment and shared project-level configuration.

| Area | Standard |
| --- | --- |
| Python | 3.13+ |
| Environment & dependencies | uv |
| DataFrames | Polars |
| Formatting | Ruff, 150-character lines, double quotes |
| Linting | Ruff |
| Docstrings | Google-style with second-line summaries |
| Type checking | Pyright, standard mode |
| Testing | pytest with strict configuration and markers |
| Coverage | Branch-aware with missing-line reporting |

Project-wide configuration is defined in `pyproject.toml` whenever the tool supports it. Editor-specific configuration should not duplicate or override project standards unnecessarily.


## Environment

Patient Zero uses `uv` to manage:

- Python versions;
- project dependencies;
- development dependencies;
- the virtual environment; and
- dependency locking.

The project currently requires Python 3.13 or later.

The expected local environment is:

```text
patient-zero/
├── .venv/
├── .python-version
├── pyproject.toml
└── uv.lock
```

`.python-version` defines the Python version used for local development.

`pyproject.toml` defines project metadata, dependencies, and tool configuration.

`uv.lock` records the resolved dependency versions.

`.venv/` contains the local virtual environment and should not be committed.


## Initial Setup

After cloning the repository, synchronize the project environment:

```bash
uv sync
```

This creates or updates `.venv` using the project configuration and lockfile.

Commands should generally be executed through the project environment using:

```bash
uv run <command>
```

Manual virtual environment activation is not required.


## Dependency Management

Runtime dependencies should be added with:

```bash
uv add <package>
```

Development-only dependencies should be added with:

```bash
uv add --dev <package>
```

Dependencies should not be installed directly into `.venv` with `pip` when they are part of the Patient Zero project.

Runtime dependencies belong in:

```toml
[project]
dependencies = [
    ...
]
```

Development dependencies belong in:

```toml
[dependency-groups]
dev = [
    ...
]
```


## Formatting

Patient Zero uses Ruff for formatting.

Current formatting standards include:

- maximum line length of 150 characters;
- double quotes;
- space-based indentation; and
- automatic line-ending handling.

Check formatting without modifying files:

```bash
uv run ruff format --check .
```

Apply formatting:

```bash
uv run ruff format .
```

Formatting rules are defined in `pyproject.toml`.


## Linting

Patient Zero uses Ruff for linting.

The current rule groups include:

| Rule | Purpose |
| --- | --- |
| `E` | pycodestyle errors |
| `F` | Pyflakes |
| `I` | import sorting |
| `UP` | modern Python syntax |
| `B` | likely bugs and design problems |
| `SIM` | unnecessary complexity |
| `D` | docstring conventions |
| `RUF` | Ruff-specific checks |

Run linting with:

```bash
uv run ruff check .
```

Apply automatically fixable changes with:

```bash
uv run ruff check . --fix
```

Automatic fixes should still be reviewed before they are committed.


## Documentation

Public modules, classes, and functions should include useful docstrings.

Patient Zero uses Google-style docstrings with multi-line summaries beginning on the second line.

Preferred:

```python
def get_patient(patient_id: str) -> Patient:
    """
    Retrieve a patient by identifier.

    Args:
        patient_id: Unique identifier for the patient.

    Returns:
        The requested patient.

    Raises:
        PatientNotFoundError: If the patient does not exist.
    """
```

The second-line summary format is intentionally enforced using Ruff rule `D213` rather than the Google convention's default `D212`.

Documentation should describe information that is useful to someone reading or using the code, including:

- purpose;
- parameters;
- return values;
- exceptions;
- assumptions;
- relevant side effects; and
- non-obvious behavior.

Comments should explain intent, reasoning, assumptions, or implementation details that are not apparent from the code itself.

Avoid comments that simply restate the following line.

For example:

```python
# Add the handler to the logger.
logger.addHandler(handler)
```

does not provide useful information.

A comment such as:

```python
# A logger may be requested by multiple consumers during the application's
# lifetime. Add the stdout handler only once to prevent duplicate output.
if not logger.handlers:
```

documents behavior that is not obvious from the code alone.

Tests are exempt from general docstring requirements when the test name adequately describes the behavior being tested.

Empty package `__init__.py` files are exempt from the public-package docstring requirement.


## Type Checking

Patient Zero uses Pyright in standard mode.

Type checking includes:

```text
p0/
etls/
dags
```

Run type checking with:

```bash
uv run pyright
```

Type hints should make interfaces and expected behavior easier to understand.

Type annotations should be used consistently for public interfaces and application code. Type complexity should not be introduced solely to satisfy the type checker when it makes the code materially harder to understand.

Pyright strict mode is not currently enabled. Type-checking requirements may become more restrictive as the codebase matures.


## Testing

Patient Zero uses pytest.

Tests are kept locally and excluded from Git:

```text
local_tests/
```

The expected structure will distinguish unit and integration testing as the test suite develops:

```text
local_tests/
├── unit/
└── integration/
```

Run the full test suite with:

```bash
uv run pytest
```

Pytest is configured with strict configuration and strict marker validation so invalid configuration or unknown markers fail rather than being silently ignored.

The currently defined markers are:

| Marker | Purpose |
| --- | --- |
| `integration` | Tests that interact with external systems or multiple application components |
| `slow` | Tests intentionally slower than the standard test suite |

Run only integration tests:

```bash
uv run pytest -m integration
```

Exclude integration tests:

```bash
uv run pytest -m "not integration"
```


## Coverage

Patient Zero uses `pytest-cov` and Coverage.py for test coverage.

Coverage is measured against:

```text
p0/
```

Branch coverage is enabled so tests measure alternative execution paths rather than only whether individual lines were executed.

Run tests with coverage:

```bash
uv run pytest --cov=p0 --cov-report=term-missing
```

Coverage reports show missing lines and omit files that are already fully covered.

Coverage is currently used to identify untested behavior rather than enforce an arbitrary repository-wide coverage percentage.


## Common Commands

```bash
# Synchronize the local environment.
uv sync

# Run linting.
uv run ruff check .

# Check formatting.
uv run ruff format --check .

# Apply formatting.
uv run ruff format .

# Run static type checking.
uv run pyright

# Run tests.
uv run pytest

# Run tests with coverage.
uv run pytest --cov=p0 --cov-report=term-missing
```


## Configuration

The primary development configuration is maintained in `pyproject.toml`.

Configuration should remain centralized there when supported by the relevant tool. VS Code workspace settings should primarily control editor behavior and integration with these tools rather than redefine project standards.
