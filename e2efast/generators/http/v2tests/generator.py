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


class ServiceTestGenerator(BaseTemplateGenerator):
    BASE_PATH = Path("") / "tests"

    def __init__(
        self,
        openapi_spec: Parser,
        templates_dir: str | Path | None = None,
        base_path: str | Path | None = None,
        base_client_import: str | None = None,
        child_client_import: str | None = None,
        fixtures_import: str | None = None,
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
        self.fixtures_import = fixtures_import or self._default_fixtures_import()
        self.models_import = self._build_models_import()

        super().__init__(templates_dir=str(templates_dir))

    def generate(self) -> None:
        self._gen_tests()
        format_file(str(self.base_path))

    def _gen_tests(self) -> None:
        service_dir = (
            self.base_path
            if self.base_path.name == self._service_module
            else self.base_path / self._service_module
        )

        self._ensure_init_file(self.base_path / "__init__.py")
        self._ensure_init_file(service_dir / "__init__.py")

        template = self.env.get_template("service_test.jinja2")
        service_fixture = f"{self._service_module}_service"

        for api_name, operations in self._operations_by_api().items():
            if not operations:
                continue

            api_dir = (
                service_dir
                if api_name is None
                else service_dir / name_to_snake(api_name)
            )
            self._ensure_init_file(api_dir / "__init__.py")

            seen_methods: set[str] = set()
            for operation in operations:
                context = self.openapi_spec.get_operation_context(operation)
                method_name = self._operation_method_name(context)
                if method_name in seen_methods:
                    continue
                seen_methods.add(method_name)

                request_body_var = (
                    name_to_snake(context.request_body_model)
                    if context.request_body_model
                    else None
                )

                models_to_import = self._collect_models(context)

                rendered_code = template.render(
                    async_mode=self.async_mode,
                    service_fixture=service_fixture,
                    service_module=self._service_module,
                    service_class=self._service_class_name(),
                    api_accessor=self._api_accessor_name(api_name),
                    method_name=method_name,
                    parameters=context.parameters,
                    request_body_model=context.request_body_model,
                    request_body_var=request_body_var,
                    call_arguments=self._call_arguments(context, request_body_var),
                    parameter_declarations=self._parameter_declarations(context),
                    fixtures_import=self.fixtures_import,
                    models_import=self.models_import,
                    models_to_import=models_to_import,
                )

                file_path = api_dir / f"test_{method_name}.py"
                if file_path.exists():
                    continue
                create_and_write_file(file_path, rendered_code)

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
    def _operation_method_name(context) -> str:
        path_snake = name_to_snake(context.path)
        return f"{context.method}_{path_snake}".strip("_")

    @staticmethod
    def _call_arguments(context, request_body_var: str | None) -> list[str]:
        arguments: list[str] = []
        if request_body_var:
            arguments.append(f"{request_body_var}={request_body_var}")

        for param in context.parameters.get("path", []):
            arguments.append(f"{param['python_name']}={param['python_name']}")
        for param in context.parameters.get("query", []):
            arguments.append(f"{param['python_name']}={param['python_name']}")
        for param in context.parameters.get("header", []):
            arguments.append(f"{param['python_name']}={param['python_name']}")

        return arguments

    @staticmethod
    def _parameter_declarations(context) -> list[dict[str, str]]:
        declarations: list[dict[str, str]] = []
        for location in ("path", "query", "header"):
            for param in context.parameters.get(location, []):
                declarations.append(
                    {
                        "name": param["python_name"],
                        "location": location,
                        "type_hint": param.get("python_type", ""),
                    }
                )
        return declarations

    def _build_models_import(self) -> str:
        return ".".join(
            [self.base_client_import, self._service_module, "models", "api_models"]
        )

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

    @staticmethod
    def _ensure_init_file(path: Path) -> None:
        if path.exists():
            return
        create_and_write_file(path, "# coding: utf-8\n")

    @staticmethod
    def _default_base_client_import() -> str:
        parts = [
            part for part in ClientGenerator.BASE_PATH.parts if part not in {"", "."}
        ]
        return ".".join(parts)

    @staticmethod
    def _default_child_client_import() -> str:
        parts = [
            part
            for part in ClientGenerator.CHILD_CLIENTS_PATH.parts
            if part not in {"", "."}
        ]
        return ".".join(parts)

    def _default_fixtures_import(self) -> str:
        parts = [
            part
            for part in (Path("framework") / "fixtures" / "http").parts
            if part not in {"", "."}
        ]
        return ".".join(parts)

    def _service_class_name(self) -> str:
        return f"{snake_to_camel(self._service_module)}Service"

    @staticmethod
    def _api_accessor_name(api_name: str | None) -> str:
        if api_name is None:
            return "default"
        return name_to_snake(api_name)

    @staticmethod
    def _api_client_class_name(api_name: str | None) -> str:
        module_name = ServiceTestGenerator._api_accessor_name(api_name)
        return f"{snake_to_camel(module_name)}Client"
