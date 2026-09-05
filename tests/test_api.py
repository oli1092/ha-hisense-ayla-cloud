"""API normalization and token-refresh unit tests."""

from datetime import datetime, timezone

import pytest

from hisense_ayla_cloud.api import AylaCloudClient, AylaAuthError


class FakeSession:
    async def request(self, *args, **kwargs):  # pragma: no cover - not used here
        raise AssertionError("network must not be used by this unit test")


class PropertyClient(AylaCloudClient):
    async def _request_json(self, method, url):
        assert url.endswith("/apiv1/dsns/dsn-1/properties.json")
        return [
            {"property": {"name": "t_power", "value": "ON", "read_only": False}},
            {"property": {"name": "f_temp_in", "value": 21.5, "read_only": True}},
        ]


def test_token_response_is_stored() -> None:
    client = AylaCloudClient(FakeSession(), "user@example.invalid", "app", "secret")
    client._set_tokens(
        {"access_token": "access", "refresh_token": "refresh", "expires_in": 3600}
    )
    assert client.refresh_token == "refresh"
    assert client.tokens is not None
    assert client.tokens.expires_at > datetime.now(timezone.utc)


def test_invalid_token_response_is_rejected() -> None:
    client = AylaCloudClient(FakeSession(), "user@example.invalid", "app", "secret")
    with pytest.raises(AylaAuthError):
        client._set_tokens({"access_token": "only-access"})


@pytest.mark.asyncio
async def test_property_response_is_normalized() -> None:
    client = PropertyClient(FakeSession(), "user@example.invalid", "app", "secret")
    properties = await client.async_get_properties("dsn-1")
    assert properties["t_power"]["value"] == "ON"
    assert properties["f_temp_in"]["read_only"] is True
