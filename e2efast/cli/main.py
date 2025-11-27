from __future__ import annotations

import click

from restcodegen.generator.parser import Parser

from e2efast.generators.http.client.generator import ClientGenerator
from e2efast.generators.http.fixtures.generator import FixtureGenerator
from e2efast.generators.http.v2fixtures.generator import ServiceFixtureGenerator
from e2efast.generators.http.tests.generator import TestGenerator
from e2efast.generators.http.v2tests.generator import ServiceTestGenerator


FIXTURE_GENERATORS = {
    "v1": FixtureGenerator,
    "v2": ServiceFixtureGenerator,
}

TEST_GENERATORS = {
    "v1": TestGenerator,
    "v2": ServiceTestGenerator,
}


@click.command()
@click.argument("service", type=str)
@click.option("--spec", "spec_url", required=True, help="OpenAPI spec URL or path")
@click.option(
    "--with-suite",
    "with_suite",
    is_flag=True,
    help="Generate fixtures and tests alongside clients",
)
@click.option(
    "--suite-version",
    "suite_version",
    type=click.Choice(["v1", "v2"]),
    default="v2",
    show_default=True,
)
def main(
    service: str,
    spec_url: str,
    with_suite: bool,
    suite_version: str,
) -> None:
    """Generate clients, fixtures, and tests for SERVICE from SPEC."""
    parser = Parser.from_source(spec_url, package_name=service)
    ClientGenerator(openapi_spec=parser, async_mode=False).generate()
    if with_suite:
        fixture_generator = FIXTURE_GENERATORS[suite_version]
        fixture_generator(openapi_spec=parser).generate()
        test_generator = TEST_GENERATORS[suite_version]
        test_generator(openapi_spec=parser, async_mode=False).generate()


if __name__ == "__main__":
    main()
