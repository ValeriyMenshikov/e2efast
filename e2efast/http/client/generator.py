from pathlib import Path

from restcodegen.generator.base import BaseTemplateGenerator
from restcodegen.generator.codegen import RESTClientGenerator
from restcodegen.generator.parser import Parser
from restcodegen.generator.utils import (
    create_and_write_file,
    name_to_snake,
)


class ClientGenerator(BaseTemplateGenerator):
    BASE_PATH = Path(".") / "internal" / "clients" / "http"
    CHILD_CLIENTS_PATH = Path(".") / "clients" / "http"

    def __init__(
        self,
        openapi_spec: Parser,
        templates_dir: str | None = None,
        async_mode: bool = False,
        base_path: str | Path | None = None,
        child_base_path: str | Path | None = None,
    ) -> None:
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        if child_base_path is None:
            self.child_base_path = Path(self.CHILD_CLIENTS_PATH)

        if base_path is None:
            base_path = Path(self.BASE_PATH)

        self.openapi_spec = openapi_spec
        self._service_name = name_to_snake(openapi_spec.service_name)
        self.rest_generator = RESTClientGenerator(
            openapi_spec=openapi_spec,
            # TODO: сделать прием шаблонов для RESTClientGenerator
            templates_dir=None,
            async_mode=async_mode,
            base_path=base_path,
        )
        super().__init__(templates_dir=str(templates_dir))

    def generate(self) -> None:
        self.rest_generator.generate()
        self._gen_child_clients()

    def _gen_child_clients(self) -> None:
        service_module = name_to_snake(self.openapi_spec.service_name)
        child_service_path = (
            self.child_base_path
            if self.child_base_path.name == service_module
            else self.child_base_path / service_module
        )

        create_and_write_file(self.child_base_path / "__init__.py", "# coding: utf-8\n")
        create_and_write_file(child_service_path / "__init__.py", "# coding: utf-8\n")

        template = self.env.get_template("client.jinja2")
        for api_name in self.openapi_spec.apis:
            rendered_code = template.render(
                api_name=api_name,
                service_name=self.openapi_spec.service_name,
                base_import=self.rest_generator._base_import,
            )
            file_path = child_service_path / f"{name_to_snake(api_name)}_client.py"
            create_and_write_file(file_path, rendered_code)
