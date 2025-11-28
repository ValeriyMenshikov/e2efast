# E2Efast

[![PyPI version](https://img.shields.io/pypi/v/e2efast.svg)](https://pypi.org/project/e2efast)
[![Python versions](https://img.shields.io/pypi/pyversions/e2efast.svg)](https://pypi.python.org/pypi/e2efast)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/ValeriyMenshikov/e2efast/python-test.yml?branch=main)](https://github.com/ValeriyMenshikov/e2efast/actions/workflows/python-test.yml)
[![Coverage Status](https://coveralls.io/repos/github/ValeriyMenshikov/e2efast/badge.svg?branch=main)](https://coveralls.io/github/ValeriyMenshikov/e2efast?branch=main)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/ValeriyMenshikov/e2efast/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/e2efast.svg)](https://pypistats.org/packages/e2efast)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

<p align="center">
  <b>Generate Python HTTP clients, fixtures, and integration tests from a single OpenAPI specification</b>
</p>

## 🚀 Overview

E2Efast wraps the `restcodegen` toolkit and adds project-specific generators that organise REST clients, user-facing facades, pytest fixtures, and optional integration tests. One CLI command keeps these artefacts in sync so teams can iterate quickly on backend contracts.

### ✨ Key Features

- **One-command workflow** – Generate clients, fixtures, and tests with a single CLI invocation.
- **Safe regeneration** – Internal clients are regenerated automatically while editable facades live under `framework/clients/http` for manual customisations.
- **Fixture suite versions** – Choose per-client fixtures (suite `v1`) or aggregated service fixtures and tests (suite `v2`).
- **Custom HTTP layer** – Override a single `ClientClass` alias to switch between `httpx.Client`, `AsyncClient`, or your own subclass across all fixtures.

## 📚 Example Project

Want to see a complete scaffold created by e2efast? Check out the sample repository: [e2efast-project-example](https://github.com/ValeriyMenshikov/e2efast-project-example).

## ⚡ Quick Start

1. Install project dependencies with Poetry:

   ```bash
   poetry install
   ```

2. Run the generator (adjust service name/spec as needed). The `--spec` option
   accepts either a local file path or an HTTP(S) URL:

   ```bash
   poetry run e2efast customers --spec ./crm_v2_service.json --with-tests
   ```

3. Open `framework/settings/base_settings.py` and update the base URL or any
   other settings you require.

4. Export the environment variables (or ensure they are provided via your
   settings loader) and start writing tests—the generated clients, fixtures, and
   tests will use the configuration automatically.

   On the first run the generator creates `framework/settings/base_settings.py`
   and, when fixtures are enabled, `tests/conftest.py`. Subsequent updates should
   be applied manually.

5. Need only clients and fixtures (without tests)? Run the same command with
   `--with-fixtures` (the `--spec` option still accepts a path or URL):

   ```bash
   poetry run e2efast customers --spec ./crm_v2_service.json --with-fixtures --suite-version v2
   ```

## 📦 Installation

Install the library itself from PyPI:

```bash
pip install e2efast
```

## 🔧 CLI Usage

Run the generator by providing the service name and OpenAPI spec location (path or URL):

```bash
poetry run e2efast customers --spec ./crm_v2_service.json --with-tests --suite-version v2
```

### Command Options

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `service` (argument) | Logical service name used for packages/modules | ✅ | – |
| `--spec` / `spec_url` | Path or URL to the OpenAPI document | ✅ | – |
| `--with-fixtures` | Generate fixtures in addition to clients | ❌ | `False` |
| `--with-tests` | Generate tests (fixtures implied) | ❌ | `False` |
| `--suite-version` | Fixture/test style: `v1` (per-client) or `v2` (service facade) | ❌ | `v2` |

The CLI parses the specification once and reuses the resulting parser for each generator, ensuring all outputs remain consistent.

## 📁 Generated Structure

```
├── framework                          # User-facing extension layer
│    ├── clients
│    │    └── http
│    │         └── <service>/          # Editable client wrappers (safe to modify)
│    ├── fixtures
│    │    └── http
│    │         ├── base.py             # Define ClientClass alias (editable)
│    │         └── <service>.py        # Generated fixtures (overwritten on regen)
│    └── settings
│         └── base_settings.py         # Pydantic settings scaffold (generated once)
│
├── internal                           # Auto-regenerated low-level clients
│    └── clients
│         └── http
│              └── <service>/
│                  ├── apis            # Generated API client classes
│                  └── models          # Pydantic models
│
└── tests                              # Generated or custom test suites
     ├── conftest.py                   # pytest plugin registration (generated once)
     └── http
          └── <service>/               # Generated test suite (if enabled)
```

Re-run the CLI whenever the OpenAPI spec changes; generated files are overwritten, while your custom facades remain intact.

## 🔄 Custom HTTP Client

Every fixture imports `ClientClass` from `framework/fixtures/http/base.py`. Update this alias to point at any `httpx.Client` subclass and regenerated fixtures automatically adopt the change.

```python
from functools import partial

import httpx

ClientClass = partial(httpx.Client, timeout=httpx.Timeout(60.0))

# Example override:
# from httpx import AsyncClient
# ClientClass = AsyncClient
```

The `base.py` file is generated only when missing, so manual overrides are preserved across subsequent runs.

## 🧩 Wiring Fixtures into pytest

Add the generated fixture package to your test suite via `pytest_plugins` so they auto-register during collection:

```python
# conftest.py
pytest_plugins = ["framework.fixtures.http.service_name"]
```

Replace `service_name` with the snake_case module generated in `framework/fixtures/http` (for example the CLI run above produces `framework/fixtures/http/customers.py`, so use `pytest_plugins = ["framework.fixtures.http.customers"]`).

## 🌐 Environment Variables

Each generated fixture module reads a service-specific base URL from `os.getenv("<SERVICE_NAME>_BASE_URL")`. Define this environment variable before running fixtures or the generated tests—for example:

```bash
export CUSTOMERS_BASE_URL="https://api.example.test"
```

The variable name is derived from the snake_case service module uppercased with `_BASE_URL` appended (e.g. `customers` → `CUSTOMERS_BASE_URL`). The expected names follow the pattern `<package_name_upper>_BASE_URL`; you can confirm the exact value inside any generated fixture (look for the `os.getenv` call).

## 🛠️ Development Workflow

```bash
poetry install           # Install dependencies
poetry run pytest        # Run tests
poetry run ruff check .  # Lint (example command)
```

Generators call `format_file` on their output directories to keep generated code tidy automatically.

## 📄 License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.