from __future__ import annotations

from pathlib import Path

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


class FixtureGenerator(BaseTemplateGenerator):
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
        self._gen_fixtures()
        self._gen_base_fixture()
        format_file(str(self.base_path))

    def _gen_base_fixture(self) -> None:
        template = self.env.get_template("base.jinja2")
        rendered = template.render(
            header=self._render_header(service_name="fixtures.base", editable=True)
        )
        create_and_write_file(self.base_path / "base.py", rendered)

    def _gen_fixtures(self) -> None:
        output_path = self._service_file_path()
        output_parent = output_path.parent

        self._ensure_init_file(
            self.base_path / "__init__.py",
            f"from . import {self._service_module}  # noqa: F401",
        )
        self._ensure_init_file(
            self.base_path.parent / "__init__.py",
            "from .http import *  # noqa: F401",
        )
        if output_parent != self.base_path:
            self._ensure_init_file(output_parent / "__init__.py")

        template = self.env.get_template("fixture.jinja2")

        fixtures: list[dict[str, str]] = []

        for api_name, operations in sorted(
            self._operations_by_api().items(), key=lambda item: (item[0] or "")
        ):
            if not api_name or not operations:
                continue

            api_module = self._api_module_name(api_name)
            client_class = self._api_client_class_name(api_name)
            fixture_name = f"{api_module}_client"

            fixtures.append(
                {
                    "api_module": api_module,
                    "api_client_class": client_class,
                    "fixture_name": fixture_name,
                }
            )

        if not fixtures:
            return

        rendered_code = template.render(
            header=self._render_header(
                service_name=self._service_module,
                editable=False,
            ),
            child_client_import=self.child_client_import,
            service_module=self._service_module,
            fixtures=fixtures,
            service_fixture_name=f"{self._service_module}_client",
        )

        create_and_write_file(output_path, rendered_code)

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

    @staticmethod
    def _ensure_init_file(path: Path, text: str | None = None) -> None:
        if path.exists():
            return
        create_and_write_file(path, text or " ")

    @staticmethod
    def _default_child_client_import() -> str:
        parts = [
            part
            for part in ClientGenerator.CHILD_CLIENTS_PATH.parts
            if part not in {"", "."}
        ]
        return ".".join(parts)

    @staticmethod
    def _api_module_name(api_name: str) -> str:
        return name_to_snake(api_name)

    @staticmethod
    def _api_client_class_name(api_name: str) -> str:
        return f"{snake_to_camel(name_to_snake(api_name))}Client"

    @staticmethod
    def _default_base_client_import() -> str:
        parts = [
            part for part in ClientGenerator.BASE_PATH.parts if part not in {"", "."}
        ]
        return ".".join(parts)

    def _service_file_path(self) -> Path:
        base = self.base_path
        if base.suffix == ".py":
            return base
        if base.name == self._service_module and base.suffix == "":
            return base.with_suffix(".py")
        return base / f"{self._service_module}.py"

    def _render_header(self, *, service_name: str, editable: bool) -> str:
        return render_header(
            self._header_template,
            version=self._tool_version,
            service_name=service_name,
            can_edit=editable,
        )
