"""FR-017: this repository produces no Tableau files and no Tableau connector code."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

REPO_ROOT = Path(__file__).resolve().parents[3]  # /repo, also in the tests container
TABLEAU_EXTENSIONS = {".twb", ".twbx", ".tbm", ".tds", ".tdsx", ".hyper"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
# Directories that hold code we write; the docs and context folders may talk about Tableau freely.
CODE_DIRS = ("backend/src", "frontend", "db")
CONNECTOR_PATTERN = re.compile(
    r"tableau\.(registerConnector|connectionName|makeConnector|submit)|tableauwdc|WebDataConnector",
    re.IGNORECASE,
)
CODE_SUFFIXES = {".py", ".js", ".mjs", ".html", ".sql", ".json", ".yml", ".yaml", ".conf"}


def walk(root: Path):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        if path.is_file():
            yield path


def test_no_tableau_files_in_the_repository() -> None:
    found = [str(p.relative_to(REPO_ROOT)) for p in walk(REPO_ROOT) if p.suffix.lower() in TABLEAU_EXTENSIONS]
    assert not found, f"Tableau files are built manually by the team, not stored here (FR-017): {found}"


def test_no_tableau_connector_code() -> None:
    offenders = []
    for directory in CODE_DIRS:
        base = REPO_ROOT / directory
        if not base.is_dir():
            continue
        for path in walk(base):
            if path.suffix.lower() in CODE_SUFFIXES and CONNECTOR_PATTERN.search(
                path.read_text(encoding="utf-8", errors="ignore")
            ):
                offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, f"Tableau connector code is out of scope (FR-017): {offenders}"


def test_the_scan_sees_the_repository() -> None:
    assert (REPO_ROOT / "docker-compose.yml").is_file() or (REPO_ROOT / "backend").is_dir()
