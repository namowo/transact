"""Broad smoke tests that guard against PRs breaking the API as a whole.

These don't check business logic; they make sure every router still imports,
the OpenAPI schema still builds and no list/read endpoint crashes with a 5xx
(e.g. because of a broken query, relationship or response model).
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.main import app


def _parameterless_get_paths() -> list[str]:
    return sorted(
        path
        for path, operations in app.openapi()["paths"].items()
        if "get" in operations and "{" not in path
    )


async def test_openapi_schema_builds(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200
    assert response.json()["paths"]


def test_routes_are_registered() -> None:
    assert len(_parameterless_get_paths()) > 10


@pytest.mark.parametrize("path", _parameterless_get_paths())
async def test_get_endpoint_does_not_crash(superuser_client: AsyncClient, path: str) -> None:
    response = await superuser_client.get(path)
    assert response.status_code < 500, f"GET {path} -> {response.status_code}: {response.text[:500]}"
