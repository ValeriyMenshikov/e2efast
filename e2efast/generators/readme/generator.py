from __future__ import annotations

from pathlib import Path

from restcodegen.generator.base import BaseTemplateGenerator
from restcodegen.generator.parser import Parser
from restcodegen.generator.utils import create_and_write_file, name_to_snake


class ReadmeGenerator(BaseTemplateGenerator):
    BASE_PATH = Path(".")
    OUTPUT_PATH = Path("README.md")

    def __init__(
        self,
        openapi_spec: Parser,
        templates_dir: str | Path | None = None,
        base_path: str | Path | None = None,
    ) -> None:
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        if base_path is None:
            base_path = self.BASE_PATH

        self.openapi_spec = openapi_spec
        self.base_path = Path(base_path)
        self._service_name = openapi_spec.service_name
        self._service_module = name_to_snake(openapi_spec.service_name)

        super().__init__(templates_dir=str(templates_dir))

        # TODO: Костылина, надо разобраться и убрать, когда будет понятно какой из генераторов генерит __init__ в корне
        core_init_path = self.BASE_PATH / "__init__.py"
        if core_init_path.exists():
            core_init_path.unlink()
        parent_init_path = self.BASE_PATH.parent / "__init__.py"
        if parent_init_path.exists() and parent_init_path != core_init_path:
            parent_init_path.unlink()

    def generate(self) -> None:
        output_path = self.base_path / self.OUTPUT_PATH
        if output_path.exists():
            return

        template = self.env.get_template("readme.md.jinja2")
        rendered = template.render(
            service_name=self._service_name,
            service_module=self._service_module,
            service_env_var=f"{self._service_module.upper()}_BASE_URL",
        )

        create_and_write_file(output_path, rendered)
