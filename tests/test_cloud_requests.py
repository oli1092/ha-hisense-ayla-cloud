"""Exercise real client request paths without user credentials or the network."""

import logging
from unittest.mock import Mock

import pytest

from hisense_ayla_cloud.api import AylaCloudClient, AylaAuthError, AylaConnectionError
from hisense_ayla_cloud.const import HISENSE_EU_APP_ID, HISENSE_EU_APP_SECRET
from hisense_ayla_cloud.safe_diagnostics import safe_property


class Response:
    def __init__(self, status, data):
        self.status, self.data = status, data
        self.headers = {}
        self.released = False

    async def json(self, **kwargs):
        return self.data

    def release(self):
        self.released = True


class Session:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    async def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def tokens(refresh="refresh", access="access"):
    return {"access_token": access, "refresh_token": refresh, "expires_in": 3600}


@pytest.mark.asyncio
async def test_write_command_uses_cloud_datapoint_and_fresh_read():
    session = Session(Response(200, [{"property": {
        "name": "t_control_value", "value": 3343616, "read_only": False}}]), Response(201, {}))
    client = AylaCloudClient(session, "test@example.invalid", "app", "secret")
    client._set_tokens(tokens())
    await client.async_command("test-device", "temperature", 24)
    method, url, args = session.calls[1]
    assert method == "POST"
    assert url == "https://ads-eu.aylanetworks.com/apiv1/dsns/test-device/properties/t_control_value/datapoints.json"
    assert args["json"] == {"datapoint": {"value": 3212288}}


@pytest.mark.asyncio
async def test_login_request_and_discovery():
    session = Session(Response(200, tokens()), Response(200, [{"device": {"dsn": "test-device"}}]))
    client = AylaCloudClient(session, "test@example.invalid", HISENSE_EU_APP_ID, HISENSE_EU_APP_SECRET)
    await client.async_login("test-password")
    assert await client.async_list_devices() == [{"dsn": "test-device"}]
    method, url, args = session.calls[0]
    assert method == "POST" and url == "https://user-field-eu.aylanetworks.com/users/sign_in.json"
    application = args["json"]["user"]["application"]
    assert application["app_id"] == "Hisense-mw-id"
    # The reference adds 'mw' to app_id only, never to the secret prefix.
    assert application["app_secret"].startswith("Hisense-")
    assert not application["app_secret"].startswith("Hisense-mw-")
    assert session.calls[1][2]["headers"]["Authorization"] == "auth_token access"


@pytest.mark.asyncio
async def test_rejected_access_refreshes_and_persists_rotated_token():
    rejected = Response(401, {})
    session = Session(rejected, Response(200, tokens("rotated", "new-access")), Response(200, []))
    client = AylaCloudClient(session, "test@example.invalid", "app", "secret")
    client._set_tokens(tokens())
    persist = Mock()
    client.on_token_change = persist
    assert await client.async_list_devices() == []
    assert rejected.released
    assert session.calls[1][2]["json"] == {"user": {"refresh_token": "refresh"}}
    assert session.calls[2][2]["headers"]["Authorization"] == "auth_token new-access"
    persist.assert_called_once_with("rotated")
    assert "new-access" not in repr(client.tokens)
    assert "rotated" not in repr(client.tokens)


@pytest.mark.asyncio
async def test_invalid_login_does_not_log_server_echo(caplog):
    session = Session(Response(401, {"message": "sensitive-password"}))
    client = AylaCloudClient(session, "test@example.invalid", "app", "secret")
    with caplog.at_level(logging.DEBUG), pytest.raises(AylaAuthError):
        await client.async_login("sensitive-password")
    assert "sensitive-password" not in caplog.text


@pytest.mark.asyncio
async def test_timeout_becomes_connection_error():
    client = AylaCloudClient(Session(TimeoutError()), "test@example.invalid", "app", "secret")
    with pytest.raises(AylaConnectionError):
        await client.async_login("unused")


def test_diagnostics_redact_unknown_values():
    assert safe_property({"name": "f_votage", "value": 230}) == {"value": 230}
    assert safe_property({"name": "f_power_display", "value": None}) == {"value": None}
    assert safe_property({"name": "f_electricity", "value": 0}) == {"value": 0}
    assert safe_property({"name": "t_control_value", "value": 123456}) == {"value": 123456}
    assert safe_property({"name": "wifi_password", "value": "sensitive"}) == {"value": "REDACTED"}
    assert safe_property({"name": "t_power", "value": "ON"}) == {"value": "ON"}
    assert safe_property({"name": "t_power", "value": {"token": "sensitive"}}) == {"value": "REDACTED"}
