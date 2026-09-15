from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
AUTH = "Bearer test-token"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_tools():
    r = client.get("/v1/tools")
    assert r.status_code == 200
    data = r.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "notify.send_one"


def test_unknown_tool():
    r = client.post(
        "/v1/tools/call",
        json={"tool": "unknown.tool", "arguments": {}},
        headers={"Authorization": AUTH},
    )
    assert r.status_code == 404


def test_invalid_national_id():
    r = client.post(
        "/v1/tools/call",
        json={
            "tool": "notify.send_one",
            "arguments": {"message": "hello", "userName": "123", "providerType": 1},
        },
        headers={"Authorization": AUTH},
    )
    assert r.status_code == 422
    assert r.json()["success"] is False


def test_invalid_provider_type():
    r = client.post(
        "/v1/tools/call",
        json={
            "tool": "notify.send_one",
            "arguments": {"message": "hello", "userName": "1234567890", "providerType": 99},
        },
        headers={"Authorization": AUTH},
    )
    assert r.status_code == 422


def test_empty_message():
    r = client.post(
        "/v1/tools/call",
        json={
            "tool": "notify.send_one",
            "arguments": {"message": "   ", "userName": "1234567890", "providerType": 1},
        },
        headers={"Authorization": AUTH},
    )
    assert r.status_code == 422


@pytest.mark.anyio
async def test_successful_send():
    with patch("app.tools.send_one._send_one", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"message": "Notification sent successfully."}
        r = client.post(
            "/v1/tools/call",
            json={
                "tool": "notify.send_one",
                "arguments": {
                    "message": "جلسه فردا",
                    "userName": "1234567890",
                    "providerType": 1,
                },
            },
            headers={"Authorization": AUTH},
        )
    assert r.status_code == 200
    assert r.json()["success"] is True


@pytest.mark.anyio
async def test_notify_api_403():
    from app.clients.notify_client import NotifyClientError

    with patch("app.tools.send_one._send_one", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = NotifyClientError(403, "NOTIFY_API_ERROR", "Notification service returned an error")
        r = client.post(
            "/v1/tools/call",
            json={
                "tool": "notify.send_one",
                "arguments": {
                    "message": "test",
                    "userName": "1234567890",
                    "providerType": 2,
                },
            },
            headers={"Authorization": AUTH},
        )
    assert r.status_code == 403
    assert r.json()["success"] is False


@pytest.mark.anyio
async def test_notify_api_500():
    from app.clients.notify_client import NotifyClientError

    with patch("app.tools.send_one._send_one", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = NotifyClientError(502, "NOTIFY_API_ERROR", "Notification service returned an error")
        r = client.post(
            "/v1/tools/call",
            json={
                "tool": "notify.send_one",
                "arguments": {
                    "message": "test",
                    "userName": "1234567890",
                    "providerType": 3,
                },
            },
            headers={"Authorization": AUTH},
        )
    assert r.status_code == 502
    assert r.json()["success"] is False
