"""The frontend's display-only season table (price preview, FR-018/FR-019) must equal the backend's rule.

Research R15 keeps business rules out of the browser; the price preview is the one deliberate mirror. The API
re-derives everything when a booking is saved, so this test only guards that the preview cannot show a season
the server would not use.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from hotel_api.business.rules.seasons import season_of_month

pytestmark = pytest.mark.architecture

REPO_ROOT = Path(__file__).resolve().parents[3]  # /repo, also in the tests container
PRICE_PREVIEW = REPO_ROOT / "frontend" / "public" / "price-preview.js"


def test_the_frontend_season_table_matches_seasons_py():
    source = PRICE_PREVIEW.read_text(encoding="utf-8")
    match = re.search(r"SEASON_BY_MONTH\s*=\s*\[([^\]]*)\]", source)
    assert match, "price-preview.js must define SEASON_BY_MONTH as an array literal (January first)"
    frontend = [item.strip().strip("\"'") for item in match.group(1).split(",")]
    assert frontend == [season_of_month(month).value for month in range(1, 13)]


def test_only_price_preview_js_knows_the_season_table():
    """app.js and api.js stay free of the mapping: they import the one mirror."""
    for name in ("app.js", "api.js"):
        text = (REPO_ROOT / "frontend" / "public" / name).read_text(encoding="utf-8")
        assert "SEASON_BY_MONTH =" not in text and '"low", "low"' not in text, f"{name} duplicates the season table"
