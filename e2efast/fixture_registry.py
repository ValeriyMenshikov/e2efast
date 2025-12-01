_PLUGINS: set[str] = set()


def register_fixture(fixture: str) -> None:
    _PLUGINS.add(fixture)


def get_fixtures() -> list[str]:
    return list(_PLUGINS)
