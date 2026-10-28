"""The contract is valid OpenAPI 3.0.3, and the app's routes match it (research R4)."""

from __future__ import annotations

import pytest
import yaml
from fastapi.routing import APIRoute
from openapi_spec_validator import validate

from hotel_api.config import Settings
from hotel_api.main import create_app
from tests.conftest import CONTRACT_PATH

pytestmark = pytest.mark.contract

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def contract_operations(spec: dict) -> set[tuple[str, str]]:
    return {
        (method.upper(), path)
        for path, item in spec["paths"].items()
        for method in item
        if method in HTTP_METHODS
    }


def app_operations() -> set[tuple[str, str]]:
    app = create_app(Settings())
    return {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
        if method not in {"HEAD", "OPTIONS"}
    }


def test_contract_is_valid_openapi_3_0_3(spec: dict) -> None:
    assert spec["openapi"] == "3.0.3"
    validate(spec)


def test_contract_has_19_operations(spec: dict) -> None:
    assert len(contract_operations(spec)) == 19


def test_every_implemented_route_is_in_the_contract(spec: dict) -> None:
    undocumented = app_operations() - contract_operations(spec)
    assert not undocumented, f"implemented but not in the contract: {sorted(undocumented)}"


@pytest.mark.xfail(reason="routers are added story by story; remove this marker in T102", strict=False)
def test_route_parity_every_contract_operation_is_implemented(spec: dict) -> None:
    assert app_operations() == contract_operations(spec)
