# Patient Zero

> Healthcare data, analytics, predictive modeling, and patient simulation, starting with Patient Zero.

## Overview

Patient Zero is a healthcare data science project that integrates data engineering, analytics, predictive modeling, and patient simulation within a single codebase.

The project uses public and synthetic healthcare data to support end-to-end development, including data ingestion, transformation, longitudinal patient representation, analytical methods, predictive modeling, model evaluation, and simulation.

A primary purpose of the project is also architectural. Patient Zero is being built to evaluate patterns for organizing a growing analytical codebase while maintaining clear ownership of data access, transformations, reusable functionality, model execution, and orchestration.

## Approach

The project is being developed incrementally. Components are introduced when they have a defined responsibility rather than creating abstractions in anticipation of future requirements.

Patient Zero currently uses factories for construction and dependency management, with registries and independently packaged components considered where their specific use cases justify them.

Digital patient and digital twin functionality is an intended capability, but not the sole focus of Patient Zero. It builds on the underlying ingestion, data modeling, analytics, and predictive modeling capabilities.

## Documentation

Detailed project documentation is maintained in [`docs/`](docs/).

- [`architecture.md`](docs/architecture.md) — application structure, responsibilities, dependency management, factories, registries, and packages
- [`development.md`](docs/development.md) — environment setup, development standards, testing, typing, formatting, and linting
- [`data.md`](docs/data.md) — data sources, ingestion, normalization, and data conventions
