from __future__ import annotations

from pathlib import Path

from restcodegen.generator.base import BaseTemplateGenerator
from restcodegen.generator.parser import Parser
from restcodegen.generator.utils import (
    create_and_write_file,
    name_to_snake,
    snake_to_camel,
    format_file,
)

from e2efast.generators.http.client.generator import ClientGenerator


class FixtureGenerator(BaseTemplateGenerator):
    BASE_PATH = Path("") / "fixtures" / "http"

    def __init__(
        self,
        openapi_spec: Parser,
        templates_dir: str | Path | None = None,
        base_path: str | Path | None = None,
        base_client_import: str | None = None,
        child_client_import: str | None = None,
        async_mode: bool = False,
    ) -> None:
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        if base_path is None:
            base_path = Path(self.BASE_PATH)

        self.openapi_spec = openapi_spec
        self.async_mode = async_mode
        self._service_module = name_to_snake(openapi_spec.service_name)
        self.base_path = Path(base_path)
        self.base_client_import = (
            base_client_import or self._default_base_client_import()
        )
        self.child_client_import = (
            child_client_import or self._default_child_client_import()
        )
        self.models_import = self._build_models_import()

        super().__init__(templates_dir=str(templates_dir))

    def generate(self) -> None:
        self._gen_fixtures()
        format_file(str(self.base_path))

    def _gen_fixtures(self) -> None:
        output_path = self._service_file_path()
        output_parent = output_path.parent

        self._ensure_init_file(self.base_path / "__init__.py")
        if output_parent != self.base_path:
            self._ensure_init_file(output_parent / "__init__.py")

        template = self.env.get_template("fixture.jinja2")

        fixtures: list[dict[str, str]] = []
        all_models: set[str] = set()

        for api_name, operations in sorted(
            self._operations_by_api().items(), key=lambda item: (item[0] or "")
        ):
            if not api_name or not operations:
                continue

            api_module = self._api_module_name(api_name)
            client_class = self._api_client_class_name(api_name)
            fixture_name = f"{api_module}_client"

            models = self._collect_models_for_operations(operations)
            all_models.update(models)

            fixtures.append(
                {
                    "api_module": api_module,
                    "api_client_class": client_class,
                    "fixture_name": fixture_name,
                    "models": models,
                }
            )

        if not fixtures:
            return

        rendered_code = template.render(
            async_mode=self.async_mode,
            child_client_import=self.child_client_import,
            service_module=self._service_module,
            fixtures=fixtures,
            models_import=self.models_import,
            models_to_import=sorted(all_models),
            service_fixture_name=f"{self._service_module}_client",
            http_client_import=self._http_client_import_name(),
            http_client_class=self._http_client_class_name(),
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
    def _ensure_init_file(path: Path) -> None:
        if path.exists():
            return
        create_and_write_file(path, "# coding: utf-8\n")

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
    def _collect_models(context) -> list[str]:
        models: set[str] = set()
        if context.request_body_model:
            models.add(context.request_body_model)
        if context.success_response and context.success_response not in {
            "Response",
            "None",
        }:
            models.add(context.success_response)
        return sorted(models)

    def _collect_models_for_operations(self, operations: list) -> list[str]:
        models: set[str] = set()
        for operation in operations:
            context = self.openapi_spec.get_operation_context(operation)
            models.update(self._collect_models(context))
        return sorted(models)

    def _build_models_import(self) -> str:
        return ".".join(
            [self.base_client_import, self._service_module, "models", "api_models"]
        )

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

    def _http_client_class_name(self) -> str:
        return "AsyncClient" if self.async_mode else "Client"

    def _http_client_import_name(self) -> str:
        return "AsyncClient" if self.async_mode else "Client"
