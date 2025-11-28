from __future__ import annotations

from pathlib import Path

from jinja2 import Template
from restcodegen.generator.base import BaseTemplateGenerator
from restcodegen.generator.parser import Parser
from restcodegen.generator.utils import create_and_write_file, name_to_snake

from e2efast.utils import get_version, render_header


class ConftestGenerator(BaseTemplateGenerator):
    BASE_PATH = Path(".")
    OUTPUT_PATH = Path("tests") / "conftest.py"
    BASE_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "base_templates"

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
        self._tool_version = get_version()

        header_template_path = self.BASE_TEMPLATES_DIR / "header.jinja2"
        self._header_template = Template(
            header_template_path.read_text(encoding="utf-8")
        )

        super().__init__(templates_dir=str(templates_dir))

    def generate(self) -> None:
        output_path = self.base_path / self.OUTPUT_PATH
        if output_path.exists():
            return

        template = self.env.get_template("conftest.jinja2")
        rendered = template.render(
            header=self._render_header(editable=True),
            service_name=self._service_module,
        )

        create_and_write_file(output_path, rendered)

    def _render_header(self, *, editable: bool) -> str:
        return render_header(
            self._header_template,
            version=self._tool_version,
            service_name=self._service_name,
            can_edit=editable,
        )
