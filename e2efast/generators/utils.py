from __future__ import annotations

from pathlib import Path


def ensure_import_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.write_text(f"{line}\n", encoding="utf-8")
        return

    existing_text = path.read_text(encoding="utf-8")
    existing_lines = [_.strip() for _ in existing_text.splitlines()]
    if line.strip() in existing_lines:
        return

    if existing_text.strip() == "":
        new_text = f"{line}\n"
    else:
        sep = "" if existing_text.endswith("\n") else "\n"
        new_text = f"{existing_text}{sep}{line}\n"
    path.write_text(new_text, encoding="utf-8")
