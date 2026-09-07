"""Async, cloud-only Ayla API client used by the integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout

from .const import EU_DEVICES_SERVER, EU_USER_SERVER

_LOGGER = logging.getLogger(__name__)

_PUBLIC_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "none",
    "User-Agent": "HiSmartLife/1.0 (Home Assistant)",
}


class AylaError(Exception):
    """Base Ayla API error."""


class AylaAuthError(AylaError):
    """Authentication was rejected or cannot be refreshed."""


class AylaRateLimitError(AylaError):
    """The cloud asked the client to slow down."""

    def __init__(self, retry_after: int | None = None) -> None:
        super().__init__("Ayla API rate limit")
        self.retry_after = retry_after


class AylaConnectionError(AylaError):
    """A network or response error occurred."""


@dataclass(slots=True)
class AylaTokens:
    """Runtime authentication state."""

    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    expires_at: datetime


class AylaCloudClient:
    """Small async client for login, discovery and property reads."""

    def __init__(self, session: ClientSession, email: str, app_id: str, app_secret: str) -> None:
        self._session = session
        self.email = email
        self._app_id = app_id
        self._app_secret = app_secret
        self._tokens: AylaTokens | None = None
        self._refresh_lock = asyncio.Lock()
        self.on_token_change: Callable[[str], None] | None = None
        self._command_locks: dict[str, asyncio.Lock] = {}

    @property
    def refresh_token(self) -> str | None:
        """Return the current refresh token for config-entry persistence."""

        return self._tokens.refresh_token if self._tokens else None

    @property
    def tokens(self) -> AylaTokens | None:
        """Expose runtime tokens to the config flow only."""

        return self._tokens

    def restore_refresh_token(self, refresh_token: str) -> None:
        """Restore a refresh token from a config entry."""

        self._tokens = AylaTokens("", refresh_token, datetime.now(timezone.utc))

    async def async_login(self, password: str) -> None:
        """Log in with the user's HiSmart Life credentials."""

        payload = {
            "user": {
                "email": self.email,
                "password": password,
                "application": {"app_id": self._app_id, "app_secret": self._app_secret},
            }
        }
        response = await self._request_raw(
            "POST",
            f"https://{EU_USER_SERVER}/users/sign_in.json",
            json=payload,
            headers=_PUBLIC_HEADERS,
        )
        data = await self._json(response)
        self._set_tokens(data)

    async def async_refresh_auth(self) -> None:
        """Refresh the access token once, serializing concurrent refreshes."""

        async with self._refresh_lock:
            if self._tokens is None or not self._tokens.refresh_token:
                raise AylaAuthError("No refresh token available")
            if self._tokens.access_token and self._tokens.expires_at > datetime.now(
                timezone.utc
            ) + timedelta(seconds=90):
                return
            response = await self._request_raw(
                "POST",
                f"https://{EU_USER_SERVER}/users/refresh_token.json",
                json={"user": {"refresh_token": self._tokens.refresh_token}},
                headers=_PUBLIC_HEADERS,
            )
            self._set_tokens(await self._json(response))

    async def async_list_devices(self) -> list[dict[str, Any]]:
        """List devices visible in the cloud account."""

        data = await self._request_json("GET", f"https://{EU_DEVICES_SERVER}/apiv1/devices.json")
        if not isinstance(data, list):
            raise AylaConnectionError("Unexpected devices response")
        return [item.get("device", item) for item in data if isinstance(item, dict)]

    async def async_get_properties(self, dsn: str) -> dict[str, dict[str, Any]]:
        """Fetch and normalize all cloud properties for one device."""

        data = await self._request_json(
            "GET", f"https://{EU_DEVICES_SERVER}/apiv1/dsns/{dsn}/properties.json"
        )
        if not isinstance(data, list):
            raise AylaConnectionError("Unexpected properties response")
        properties: dict[str, dict[str, Any]] = {}
        for item in data:
            prop = item.get("property", item) if isinstance(item, dict) else {}
            name = prop.get("name")
            if isinstance(name, str) and name:
                properties[name] = dict(prop)
        return properties

    async def async_write_property(self, dsn: str, name: str, value: int) -> None:
        """Submit one cloud datapoint; never retry ambiguous network failures."""
        await self._request_json(
            "POST",
            f"https://{EU_DEVICES_SERVER}/apiv1/dsns/{quote(dsn, safe='')}/properties/{quote(name, safe='')}/datapoints.json",
            json={"datapoint": {"value": value}},
        )

    async def async_command(self, dsn: str, command: str, value: Any) -> None:
        """Serialize fresh read/modify/write operations for one device."""
        from .commands import build_command
        async with self._command_locks.setdefault(dsn, asyncio.Lock()):
            properties = await self.async_get_properties(dsn)
            name, packed = build_command(properties, command, value)
            await self.async_write_property(dsn, name, packed)

    async def _request_json(self, method: str, url: str, **kwargs: Any) -> Any:
        """Make an authenticated request, refreshing and retrying once on 401."""

        await self.async_refresh_auth()
        for attempt in range(2):
            token = self._tokens.access_token if self._tokens else ""
            try:
                response = await self._session.request(
                    method,
                    url,
                    headers={**_PUBLIC_HEADERS, "Authorization": f"auth_token {token}"},
                    timeout=ClientTimeout(total=30),
                    **kwargs,
                )
            except (ClientError, TimeoutError) as err:
                raise AylaConnectionError("Ayla request failed") from err
            if response.status in (401, 403):
                response.release()
                if attempt == 0:
                    await self._force_refresh()
                    continue
                raise AylaAuthError("Ayla access token rejected")
            if response.status == 429:
                retry_after = response.headers.get("Retry-After")
                response.release()
                raise AylaRateLimitError(
                    int(retry_after) if retry_after and retry_after.isdigit() else None
                )
            if response.status >= 400:
                status = response.status
                response.release()
                raise AylaConnectionError(f"Ayla returned HTTP {status}")
            if method == "POST":
                response.release()
                return None
            return await self._json(response)
        raise AylaAuthError("Ayla access token rejected")

    async def _force_refresh(self) -> None:
        async with self._refresh_lock:
            if self._tokens is None or not self._tokens.refresh_token:
                raise AylaAuthError("No refresh token available")
            response = await self._request_raw(
                "POST",
                f"https://{EU_USER_SERVER}/users/refresh_token.json",
                json={"user": {"refresh_token": self._tokens.refresh_token}},
                headers=_PUBLIC_HEADERS,
            )
            self._set_tokens(await self._json(response))

    async def _request_raw(self, method: str, url: str, **kwargs: Any) -> ClientResponse:
        try:
            response = await self._session.request(method, url, timeout=ClientTimeout(total=30), **kwargs)
        except (ClientError, TimeoutError) as err:
            raise AylaConnectionError("Ayla request failed") from err
        if response.status in (401, 403):
            response.release()
            _LOGGER.debug("Ayla authentication rejected: HTTP %s", response.status)
            raise AylaAuthError("Ayla authentication rejected")
        if response.status == 429:
            retry_after = response.headers.get("Retry-After")
            response.release()
            raise AylaRateLimitError(int(retry_after) if retry_after and retry_after.isdigit() else None)
        if response.status >= 400:
            _LOGGER.debug("Ayla request rejected: HTTP %s", response.status)
            response.release()
            raise AylaConnectionError(f"Ayla returned HTTP {response.status}")
        return response

    async def _json(self, response: ClientResponse) -> Any:
        try:
            return await response.json(content_type=None)
        except (ValueError, ClientError, TimeoutError) as err:
            raise AylaConnectionError("Invalid Ayla JSON response") from err
        finally:
            response.release()

    def _set_tokens(self, data: dict[str, Any]) -> None:
        if not isinstance(data, dict) or not data.get("access_token") or not data.get("refresh_token"):
            raise AylaAuthError("Ayla response did not contain usable tokens")
        expires_in = data.get("expires_in", 3600)
        try:
            expires_seconds = max(60, int(expires_in))
        except (TypeError, ValueError):
            expires_seconds = 3600
        self._tokens = AylaTokens(
            str(data["access_token"]),
            str(data["refresh_token"]),
            datetime.now(timezone.utc) + timedelta(seconds=expires_seconds),
        )
        if self.on_token_change is not None:
            self.on_token_change(self._tokens.refresh_token)
