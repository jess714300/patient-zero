# Architecture

## Overview

Patient Zero separates code according to functional responsibility. The goal is to keep data access, transformation, application logic, modeling, and orchestration distinct while allowing those components to share common infrastructure.

The architecture is intentionally incremental. Components should be introduced when they have a defined responsibility rather than creating abstractions in anticipation of future requirements.

The current design uses factories for object construction and dependency management. Registries and independently packaged components may be used where their specific use cases justify them.

## Components

### Domain

`p0/domain/` defines the core objects and concepts used throughout Patient Zero.

Domain code represents healthcare and application concepts without containing database, API, or orchestration logic.

Expected examples include:

- patients;
- encounters;
- conditions;
- observations;
- predictions; and
- patient state.

Domain objects should remain independent of the technical systems used to create, retrieve, or persist them.

### Services

`p0/services/` contains reusable application functionality.

Planned services include:

- `ClinicalDataService`;
- `AnalyticsService`;
- `PredictiveModelService`; and
- `DigitalTwinService`.

Services may depend on other services, repositories, or infrastructure components. Dependencies should be provided to a service rather than constructed internally.

A service should own a defined capability rather than act as a general location for related functions.

### Factories

`p0/factories/` is responsible for constructing shared application objects and managing their dependencies.

The initial design will use a `ServiceFactory` with lazy initialization. A service is created when it is first requested and the same instance is returned for subsequent requests.

Conceptually:

```python
@property
def clinical_data_service(self):
    if self._clinical_data_service is None:
        self._clinical_data_service = ClinicalDataService(
            database_service=self.database_service,
            api_service=self.api_service,
        )

    return self._clinical_data_service
```

This allows dependencies to be defined centrally while preventing individual services from constructing their own copies of shared resources.

As persistence requirements develop, a separate `RepoFactory` may be introduced to manage repositories and shared database resources.

### Infrastructure

`p0/infrastructure/` contains implementations that interact with systems outside the core application.

Expected infrastructure includes:

- database connections;
- HTTP/API clients;
- file and object storage;
- external healthcare data sources; and
- other technical integrations.

Infrastructure code owns the mechanics of interacting with these systems. It should not own healthcare-specific analytical or modeling logic.

For example, an API client may understand authentication, requests, pagination, retries, and response handling. It should not determine whether a clinical event contributes to a patient's predicted hospitalization risk.

### Repositories

Repositories will provide the data-access boundary between application functionality and persistent storage when the database layer is implemented.

A repository understands how a particular type of data is stored and retrieved.

For example:

```python
patient_repo.get(patient_id)
patient_repo.save(patient)

observation_repo.get_for_patient(
    patient_id=patient_id,
    as_of=index_date,
)
```

Repositories should not own the application logic that uses the retrieved data.

If repositories become numerous or require shared resources, they may be managed through a `RepoFactory`.

### Helpers

`p0/helpers/` contains reusable, stateless functionality that does not require object lifecycle or dependency management.

Expected examples include:

- date handling;
- type conversion;
- validation;
- DataFrame utilities;
- common calculations; and
- reusable ETL functions.

Helpers should remain small and focused. Healthcare-specific application logic should not be moved into helpers simply because it is reusable.

### ETLs

`etls/` contains data ingestion and transformation processes.

ETLs are responsible for extracting, transforming, and loading data. They may use infrastructure, repositories, services, and helpers as needed.

ETLs should own transformation logic but should not own workflow orchestration.

Expected ETL categories include:

- source ingestion;
- normalization;
- clinical feature construction;
- analytical feature construction; and
- predictive target construction.

### DAGs

`dags/` defines workflow dependencies and execution order.

DAGs determine:

- what runs;
- when it runs;
- which arguments are passed to executable processes; and
- which upstream processes must complete before downstream work begins.

DAGs should coordinate ETLs and other executable processes rather than contain the underlying transformation, analytical, or modeling logic.

### Loggers

`p0/loggers/` provides consistent logging behavior across Patient Zero.

Services, ETLs, DAGs, and other application components should use the shared logging configuration rather than independently configuring Python logging.

Logging should support consistent terminal output, log levels, timestamps, component identification, and exception reporting.

### Exceptions

`p0/exceptions/` contains Patient Zero-specific exceptions.

Custom exceptions should be introduced when they provide meaningful information about application behavior or allow callers to handle known failure conditions explicitly.

## Dependency Management

Patient Zero uses dependency injection for components that rely on shared application resources.

Services should receive their dependencies rather than construct them internally. Shared services will be constructed and managed centrally by the `ServiceFactory`.

The initial dependency graph is expected to resemble:

```text
ServiceFactory
│
├── Database / persistence infrastructure
├── API infrastructure
├── ClinicalDataService
│   └── repositories / infrastructure
├── AnalyticsService
│   └── clinical data
├── PredictiveModelService
│   ├── clinical data
│   └── analytics
└── DigitalTwinService
    ├── clinical data
    ├── analytics
    └── predictive models
```

This is a starting point rather than a fixed dependency graph. Dependencies will be defined as each component is implemented.

## Factories, Registries, and Packages

Factories, registries, and packages solve different problems and are not treated as competing approaches within Patient Zero.

### Factories

Factories are used when the problem is object construction and dependency management.

The `ServiceFactory` is responsible for constructing shared application services and providing their required dependencies.

A `RepoFactory` may serve the same purpose for repositories if the persistence layer becomes sufficiently complex.

### Registries

Registries are appropriate when the problem is selecting or discovering one implementation from multiple available implementations.

Potential examples include:

```text
MODEL_REGISTRY
├── logistic_regression
├── random_forest
└── xgboost
```

or:

```text
ETL_REGISTRY
├── patients
├── encounters
├── conditions
└── observations
```

A registry should not replace dependency management when the actual requirement is constructing interconnected application objects.

### Packages

Packages provide boundaries for code that can be independently reused, versioned, or deployed.

Patient Zero will begin as a cohesive application. Components may be separated into independent packages if their reuse, dependency, or deployment requirements justify that separation.

Package boundaries should emerge from demonstrated requirements rather than being created before those requirements exist.

## Project Structure

```text
patient-zero/
├── dags/               # Workflow orchestration and execution dependencies
├── docs/               # Project documentation
├── etls/               # Data ingestion and transformation
├── p0/
│   ├── domain/         # Core healthcare objects and concepts
│   ├── exceptions/     # Patient Zero-specific exceptions
│   ├── factories/      # Object construction and dependency management
│   ├── helpers/        # Shared stateless functionality
│   ├── infrastructure/ # Databases, APIs, files, and external systems
│   ├── loggers/        # Shared logging configuration
│   └── services/       # Reusable application functionality
└── tests/              # Unit and integration tests
```

The repository structure is expected to evolve as implementation requirements become clearer. New layers or abstractions should have a defined responsibility before they are introduced.
