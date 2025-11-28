import importlib.metadata
from functools import cache
from jinja2 import Template
from markupsafe import Markup


@cache
def get_dependencies() -> list[dict[str, str]]:
    deps = [
        {"path": dep.name, "version": dep.version}
        for dep in importlib.metadata.distributions()
    ]  # type: ignore[attr-defined]

    return sorted(deps, key=lambda x: x["path"].lower())


@cache
def get_version() -> str:
    deps = get_dependencies()
    for dep in deps:
        if dep["path"] == "restcodegen":
            return dep["version"]
    return "unknown"


def render_header(
    template: Template,
    *,
    version: str,
    service_name: str | None = None,
    can_edit: bool,
) -> Markup:
    context = {"version": version, "can_edit": can_edit}
    if service_name is not None:
        context["service_name"] = service_name
    rendered = template.render(**context)
    if not rendered.endswith("\n\n"):
        rendered = rendered.rstrip("\n") + "\n\n"
    return Markup(rendered)
