from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Template
from restcodegen.generator.base import BaseTemplateGenerator
from restcodegen.generator.parser import Parser
from restcodegen.generator.utils import (
    create_and_write_file,
    name_to_snake,
    snake_to_camel,
    format_file,
)

from e2efast.generators.http.client.generator import ClientGenerator
from e2efast.utils import get_version, render_header


class ServiceFixtureGenerator(BaseTemplateGenerator):
    BASE_PATH = Path("") / "framework" / "fixtures" / "http"
    BASE_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "base_templates"

    def __init__(
        self,
        openapi_spec: Parser,
        templates_dir: str | Path | None = None,
        base_path: str | Path | None = None,
        base_client_import: str | None = None,
        child_client_import: str | None = None,
    ) -> None:
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        if base_path is None:
            base_path = Path(self.BASE_PATH)

        self.openapi_spec = openapi_spec
        self._service_module = name_to_snake(openapi_spec.service_name)
        self.base_path = Path(base_path)
        self.base_client_import = (
            base_client_import or self._default_base_client_import()
        )
        self.child_client_import = (
            child_client_import or self._default_child_client_import()
        )
        self._tool_version = get_version()
        header_template_path = self.BASE_TEMPLATES_DIR / "header.jinja2"
        self._header_template = Template(
            header_template_path.read_text(encoding="utf-8")
        )
        super().__init__(templates_dir=str(templates_dir))

    def generate(self) -> None:
        self._gen_service_fixture()
        self._gen_base_fixture()
        format_file(str(self._output_path()))

    def _gen_base_fixture(self) -> None:
        template = self.env.get_template("base.jinja2")
        rendered = template.render(
            header=self._render_header(service_name="fixtures.base", editable=True)
        )
        create_and_write_file(self.base_path / "base.py", rendered)

    def _gen_service_fixture(self) -> None:
        template = self.env.get_template("fixture.jinja2")

        clients = self._collect_clients()
        if not clients:
            return

        create_and_write_file(
            self.base_path / "__init__.py",
            f"from . import {self._service_module}_service  # noqa: F401",
        )
        create_and_write_file(
            self.base_path.parent / "__init__.py",
            "from .http import *  # noqa: F401",
        )
        rendered = template.render(
            header=self._render_header(
                service_name=self._service_module,
                editable=False,
            ),
            service_module=self._service_module,
            service_class=self._service_class_name(),
            service_fixture_name=f"{self._service_module}_service",
            base_fixture_module=self._service_module,
            child_client_import=self.child_client_import,
            clients=clients,
        )

        create_and_write_file(self._output_path(), rendered)

    def _collect_clients(self) -> list[dict[str, Any]]:
        clients: list[dict[str, Any]] = []
        seen_modules: set[str] = set()

        for api_name, operations in sorted(
            self._operations_by_api().items(), key=lambda item: (item[0] or "")
        ):
            if not operations and api_name is not None:
                continue

            module = self._api_module_name(api_name)
            if module in seen_modules:
                continue
            seen_modules.add(module)

            clients.append(
                {
                    "api_module": module,
                    "api_client_class": self._api_client_class_name(api_name),
                    "attribute_name": module,
                }
            )

        return clients

    def _operations_by_api(self) -> dict[str | None, list]:
        api_map: dict[str | None, list] = {}
        apis = list(self.openapi_spec.apis)
        if apis:
            for api_name in apis:
                api_map[api_name] = list(self.openapi_spec.handlers_by_tag(api_name))

        if not api_map:
            api_map[None] = list(self.openapi_spec.operations)
        else:
            all_known_ids = {id(op) for ops in api_map.values() for op in ops}
            extra_ops = [
                operation
                for operation in self.openapi_spec.operations
                if id(operation) not in all_known_ids
            ]
            if extra_ops:
                api_map.setdefault(None, []).extend(extra_ops)
        return api_map

    def _output_path(self) -> Path:
        base = self.base_path
        if base.suffix == ".py":
            return base
        filename = f"{self._service_module}_service.py"
        return base / filename

    def _service_class_name(self) -> str:
        return f"{snake_to_camel(self._service_module)}Service"

    def _service_fixture_name(self) -> str:
        return f"{self._service_module}_service"

    @staticmethod
    def _default_base_client_import() -> str:
        parts = [
            part for part in ClientGenerator.BASE_PATH.parts if part not in {"", "."}
        ]
        return ".".join(parts)

    def _render_header(self, *, service_name: str, editable: bool) -> str:
        return render_header(
            self._header_template,
            version=self._tool_version,
            service_name=service_name,
            can_edit=editable,
        )

    @staticmethod
    def _default_child_client_import() -> str:
        parts = [
            part
            for part in ClientGenerator.CHILD_CLIENTS_PATH.parts
            if part not in {"", "."}
        ]
        return ".".join(parts)

    @staticmethod
    def _api_module_name(api_name: str | None) -> str:
        if api_name is None:
            return "default"
        return name_to_snake(api_name)

    @staticmethod
    def _api_client_class_name(api_name: str | None) -> str:
        module_name = ServiceFixtureGenerator._api_module_name(api_name)
        return f"{snake_to_camel(module_name)}Client"
