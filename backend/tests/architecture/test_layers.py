"""Layer rules (research R3): calls go presentation -> business -> data; business knows no HTTP or SQL."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

SRC = Path(__file__).resolve().parents[2] / "src" / "hotel_api"
ROOT = "hotel_api"

# layer -> (forbidden module prefixes)
FORBIDDEN: dict[str, tuple[str, ...]] = {
    "presentation": (f"{ROOT}.data",),
    "business": (f"{ROOT}.presentation", f"{ROOT}.data", "fastapi", "starlette", "pymysql"),
    "data": (f"{ROOT}.presentation", f"{ROOT}.business.services"),
}


def imported_modules(source: str, module: str) -> set[str]:
    """Absolute names of every module imported anywhere in `source` (relative imports resolved)."""
    found: set[str] = set()
    package = module.split(".")[:-1]
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - node.level + 1]
                name = ".".join(base + ([node.module] if node.module else []))
            else:
                name = node.module or ""
            found.add(name)
            found.update(f"{name}.{alias.name}" for alias in node.names)
    return found


def violations(layer: str, source: str, module: str) -> list[str]:
    forbidden = FORBIDDEN[layer]
    return sorted(
        name
        for name in imported_modules(source, module)
        if any(name == bad or name.startswith(bad + ".") for bad in forbidden)
    )


def layer_files(layer: str) -> list[Path]:
    return sorted((SRC / layer).rglob("*.py"))


def module_name(path: Path) -> str:
    return ".".join([ROOT, *path.relative_to(SRC).with_suffix("").parts])


@pytest.mark.parametrize("layer", sorted(FORBIDDEN))
def test_layer_imports_respect_the_boundaries(layer: str) -> None:
    files = layer_files(layer)
    assert files, f"no modules found for layer {layer!r}"
    problems = {
        str(path.relative_to(SRC)): found
        for path in files
        if (found := violations(layer, path.read_text(encoding="utf-8"), module_name(path)))
    }
    assert not problems, f"{layer} layer imports forbidden modules: {problems}"


def test_the_detector_flags_each_forbidden_import() -> None:
    assert violations("presentation", "from hotel_api.data.connection import open_connection", f"{ROOT}.presentation.x")
    assert violations("business", "import pymysql", f"{ROOT}.business.x")
    assert violations("business", "from fastapi import FastAPI", f"{ROOT}.business.x")
    assert violations("business", "from hotel_api.presentation.api import errors", f"{ROOT}.business.x")
    assert violations("business", "from hotel_api import data", f"{ROOT}.business.x")
    assert violations("data", "from hotel_api.business.services.health_service import HealthService", f"{ROOT}.data.x")
    assert violations("data", "from hotel_api.presentation.api import errors", f"{ROOT}.data.x")
    assert violations("business", "from ...data import connection", f"{ROOT}.business.rules.x")


def test_the_detector_allows_the_permitted_imports() -> None:
    assert not violations("data", "from hotel_api.business.domain.models import Booking", f"{ROOT}.data.repositories.x")
    assert not violations("data", "from hotel_api.business.ports import BookingRepository", f"{ROOT}.data.x")
    assert not violations("presentation", "from hotel_api.business.services.x import Y", f"{ROOT}.presentation.x")
    assert not violations("business", "from hotel_api.business.rules import numbers", f"{ROOT}.business.services.x")
