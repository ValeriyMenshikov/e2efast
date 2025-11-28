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

- **One-command workflow** – Generate clients, fixtures, and tests with a single CLI invocation.@e2efast/cli/main.py#25-54
- **Safe regeneration** – Internal clients are regenerated automatically while editable facades live under `framework/clients/http` for manual customisations.
- **Fixture suite versions** – Choose per-client fixtures (suite `v1`) or aggregated service fixtures and tests (suite `v2`).
- **Custom HTTP layer** – Override a single `ClientClass` alias to switch between `httpx.Client`, `AsyncClient`, or your own subclass across all fixtures.

## 📦 Installation

Install project dependencies with Poetry:

```bash
poetry install
```

## 🔧 CLI Usage

Run the generator by providing the service name and OpenAPI spec location:

```bash
poetry run e2efast customers --spec ./crm_v2_service.json
```

Generate fixtures alongside the clients:

```bash
poetry run e2efast customers --spec ./crm_v2_service.json --with-fixtures --suite-version v2
```

Add service-oriented tests (fixtures implied):

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

The CLI parses the specification once and reuses the resulting parser for each generator, ensuring all outputs remain consistent.@e2efast/cli/main.py#41-54

## 📁 Generated Structure

```
framework/
  clients/http/        # Editable facade clients (safe to modify)
  fixtures/http/       # Generated pytest fixtures + base ClientClass hook
internal/
  clients/http/        # Auto-generated REST clients and models
tests/
  http/               # Optional pytest suite generated when --with-tests is enabled
```

Re-run the CLI whenever the OpenAPI spec changes; generated files are overwritten, while your custom facades remain intact.

## 🔄 Custom HTTP Client

Every fixture imports `ClientClass` from `framework/fixtures/http/base.py`. Update this alias to point at any `httpx.Client` subclass and regenerated fixtures automatically adopt the change.@e2efast/generators/http/fixtures/templates/fixture.jinja2#1-18@e2efast/generators/http/v2fixtures/templates/fixture.jinja2#1-12

```python
import httpx

ClientClass = httpx.Client

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

The variable name is derived from the snake_case service module uppercased with `_BASE_URL` appended (e.g. `customers` → `CUSTOMERS_BASE_URL`).

## 🛠️ Development Workflow

```bash
poetry install           # Install dependencies
poetry run pytest        # Run tests
poetry run ruff check .  # Lint (example command)
```

Generators call `format_file` on their output directories to keep generated code tidy automatically.

## 📄 License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.