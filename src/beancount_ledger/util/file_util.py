
from pathlib import Path

def from_file(path: Path, create_if_missing: bool = False) -> list[str]:
    if create_if_missing and not path.exists():
        path.touch()
    with path.open() as f:
        return [line.strip() for line in f if line.strip()]

def set_from_file(path: Path, create_if_missing: bool = False) -> set[str]:
    return set(from_file(path, create_if_missing=create_if_missing))
