from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.notify import SendOneArguments

logger = logging.getLogger(__name__)

_NOTIFY_ERROR_MAP: dict[int, int] = {
    400: 400,
    401: 401,
    403: 403,
    404: 404,
    422: 422,
    429: 429,
}


def _get_client(authorization: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.notify_base_url,
        headers={"Authorization": authorization, "Content-Type": "application/json"},
        timeout=httpx.Timeout(
            connect=settings.notify_connect_timeout,
            read=settings.notify_read_timeout,
            write=settings.notify_read_timeout,
            pool=settings.notify_connect_timeout,
        ),
    )


async def send_one(args: SendOneArguments, authorization: str) -> dict[str, Any]:
    sending_date = args.sendingDate
    if sending_date is None and settings.default_sending_date_to_now:
        sending_date = datetime.now(timezone.utc)

    payload: dict[str, Any] = {
        "message": args.message,
        "userName": args.userName,
        "providerType": int(args.providerType),
        "priority": args.priority,
    }
    if args.subject is not None:
        payload["subject"] = args.subject
    if sending_date is not None:
        payload["sendingDate"] = sending_date.isoformat()

    async with _get_client(authorization) as client:
        try:
            response = await client.post(
                "/api/v1/panel/notifications/sendOne",
                json=payload,
            )
        except httpx.ConnectTimeout:
            logger.error("notify_api connect timeout")
            raise NotifyClientError(503, "NOTIFY_TIMEOUT", "Connection to notification service timed out")
        except httpx.ReadTimeout:
            logger.error("notify_api read timeout")
            raise NotifyClientError(503, "NOTIFY_TIMEOUT", "Notification service did not respond in time")
        except httpx.RequestError as exc:
            logger.error("notify_api request error: %s", type(exc).__name__)
            raise NotifyClientError(502, "NOTIFY_UNREACHABLE", "Could not reach notification service")

    if response.status_code == 200 or response.status_code == 201:
        return {"message": "Notification sent successfully."}

    mapped_status = _NOTIFY_ERROR_MAP.get(response.status_code, 502 if response.status_code < 500 else 503)
    logger.warning(
        "notify_api returned %d → mapped to %d",
        response.status_code,
        mapped_status,
    )
    raise NotifyClientError(mapped_status, "NOTIFY_API_ERROR", "Notification service returned an error")


class NotifyClientError(Exception):
    def __init__(self, http_status: int, code: str, message: str) -> None:
        self.http_status = http_status
        self.code = code
        self.message = message
        super().__init__(message)
