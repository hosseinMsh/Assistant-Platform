from __future__ import annotations

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.gateway import ToolInfo

client = TestClient(app)
AUTH = "Bearer test-token"

MOCK_TOOL = ToolInfo(
    name="notify.send_one",
    server="notify",
    description="Send one notification",
    input_schema={},
)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_tools_returns_catalog():
    with patch("app.api.routes.tools.registry") as mock_reg:
        mock_reg.get_tools = AsyncMock(return_value=[MOCK_TOOL])
        r = client.get("/v1/tools")
    assert r.status_code == 200
    tools = r.json()["tools"]
    assert any(t["name"] == "notify.send_one" for t in tools)


def test_unknown_tool_returns_404():
    with patch("app.routing.router.registry") as mock_reg:
        mock_reg.find_tool = AsyncMock(return_value=None)
        r = client.post(
            "/v1/tools/call",
            json={"tool": "no.such.tool", "arguments": {}},
            headers={"Authorization": AUTH},
        )
    assert r.status_code == 404


def test_missing_authorization():
    r = client.post("/v1/tools/call", json={"tool": "notify.send_one", "arguments": {}})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_successful_forwarding():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "tool": "notify.send_one", "data": {"message": "sent"}}

    with patch("app.routing.router.registry") as mock_reg, \
         patch("app.routing.router.httpx.AsyncClient") as mock_client_cls:
        mock_reg.find_tool = AsyncMock(return_value=MOCK_TOOL)
        mock_reg.get_base_url = MagicMock(return_value="http://mcp-notify:8080")
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_instance

        r = client.post(
            "/v1/tools/call",
            json={"tool": "notify.send_one", "arguments": {"message": "test", "userName": "1234567890", "providerType": 1}},
            headers={"Authorization": AUTH},
        )

    assert r.status_code == 200
    assert r.json()["success"] is True


@pytest.mark.anyio
async def test_server_unavailable():
    import httpx as real_httpx

    with patch("app.routing.router.registry") as mock_reg, \
         patch("app.routing.router.httpx.AsyncClient") as mock_client_cls:
        mock_reg.find_tool = AsyncMock(return_value=MOCK_TOOL)
        mock_reg.get_base_url = MagicMock(return_value="http://mcp-notify:8080")
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.post = AsyncMock(side_effect=real_httpx.ConnectTimeout("timeout"))
        mock_client_cls.return_value = mock_instance

        r = client.post(
            "/v1/tools/call",
            json={"tool": "notify.send_one", "arguments": {}},
            headers={"Authorization": AUTH},
        )

    assert r.status_code == 504


def test_token_forwarded():
    """Authorization header must be forwarded to upstream."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "tool": "notify.send_one", "data": {}}

    captured = {}

    async def fake_post(url, json, headers):
        captured["auth"] = headers.get("Authorization")
        return mock_response

    with patch("app.routing.router.registry") as mock_reg, \
         patch("app.routing.router.httpx.AsyncClient") as mock_client_cls:
        mock_reg.find_tool = AsyncMock(return_value=MOCK_TOOL)
        mock_reg.get_base_url = MagicMock(return_value="http://mcp-notify:8080")
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.post = fake_post
        mock_client_cls.return_value = mock_instance

        client.post(
            "/v1/tools/call",
            json={"tool": "notify.send_one", "arguments": {}},
            headers={"Authorization": "Bearer my-secret-token"},
        )

    assert captured.get("auth") == "Bearer my-secret-token"
