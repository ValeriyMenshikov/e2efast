from __future__ import annotations

import ast
from pathlib import Path

from jinja2 import Template
from restcodegen.generator.base import BaseTemplateGenerator
from restcodegen.generator.parser import Parser
from restcodegen.generator.utils import create_and_write_file, name_to_snake

from e2efast.utils import get_version, render_header


class SettingsGenerator(BaseTemplateGenerator):
    BASE_PATH = Path("framework") / "settings"
    OUTPUT_PATH = Path("base_settings.py")
    BASE_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "base_templates"

    def __init__(
        self,
        openapi_spec: Parser,
        templates_dir: str | Path | None = None,
        base_path: str | Path | None = None,
    ) -> None:
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        self.openapi_spec = openapi_spec
        self.base_path = Path(base_path or self.BASE_PATH)
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
        output_path.parent.mkdir(parents=True, exist_ok=True)

        template = self.env.get_template("settings.jinja2")
        rendered = template.render(
            header=self._render_header(editable=True),
            service_module=self._service_module,
            service_env_var=self._service_env_var,
        )

        if not output_path.exists():
            create_and_write_file(output_path, rendered)
            return

        self._append_field_if_missing(output_path)

    @property
    def _service_env_var(self) -> str:
        return f"{self._service_module.upper()}_BASE_URL"

    def _render_header(self, *, editable: bool) -> str:
        return render_header(
            self._header_template,
            version=self._tool_version,
            service_name=self._service_name,
            can_edit=editable,
        )

    def _append_field_if_missing(self, output_path: Path) -> None:
        existing_content = output_path.read_text(encoding="utf-8")

        try:
            module = ast.parse(existing_content, type_comments=True)
        except SyntaxError:
            # If the file was heavily modified, fall back to no-op to avoid breaking user code.
            return

        settings_class = None
        for node in module.body:
            if isinstance(node, ast.ClassDef) and node.name == "Settings":
                settings_class = node
                break

        if settings_class is None:
            return

        for node in settings_class.body:
            if isinstance(node, ast.AnnAssign):
                target = node.target
                if isinstance(target, ast.Name) and target.id == self._service_module:
                    return

        indent = "    "
        for node in settings_class.body:
            if hasattr(node, "col_offset"):
                indent = " " * node.col_offset
                break

        insert_after_line = max(
            getattr(node, "end_lineno", settings_class.lineno) for node in settings_class.body
        )

        lines = existing_content.splitlines(keepends=True)

        # Ensure we insert before trailing blank lines inside the class body.
        insert_index = insert_after_line
        while (
            insert_index < len(lines)
            and lines[insert_index].strip() == ""
            and lines[insert_index - 1].startswith(indent)
        ):
            insert_index += 1

        field_template = self.env.get_template("field.jinja2")
        field_block = field_template.render(
            indent=indent,
            service_module=self._service_module,
            service_env_var=self._service_env_var,
        )

        updated_content = "".join(
            lines[:insert_index] + [field_block] + lines[insert_index:]
        )
        output_path.write_text(updated_content, encoding="utf-8")
