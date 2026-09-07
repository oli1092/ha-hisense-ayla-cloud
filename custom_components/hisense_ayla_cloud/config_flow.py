"""Config flow for HiSmart Life / Ayla cloud."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AylaAuthError, AylaCloudClient, AylaConnectionError, AylaRateLimitError
from .const import (
    CONF_APP_CODE,
    CONF_DEVICE_DSNS,
    CONF_EMAIL,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    DEFAULT_APP_CODE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    HISENSE_EU_APP_ID,
    HISENSE_EU_APP_SECRET,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class HisenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle initial setup and reauthentication."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            app_code = user_input[CONF_APP_CODE].strip().lower()
            if app_code != DEFAULT_APP_CODE:
                errors["base"] = "unsupported_app"
            else:
                client = AylaCloudClient(
                    async_get_clientsession(self.hass),
                    user_input[CONF_EMAIL].strip(),
                    HISENSE_EU_APP_ID,
                    HISENSE_EU_APP_SECRET,
                )
                try:
                    await client.async_login(user_input[CONF_PASSWORD])
                    devices = await client.async_list_devices()
                except AylaAuthError as err:
                    _LOGGER.warning("HiSmart Life login was rejected: %s", err)
                    errors["base"] = "invalid_auth"
                except (AylaConnectionError, AylaRateLimitError) as err:
                    _LOGGER.warning("HiSmart Life cloud could not be reached: %s", err)
                    errors["base"] = "cannot_connect"
                except Exception:  # noqa: BLE001 - flow must remain renderable
                    _LOGGER.exception("Unexpected Hisense Ayla setup failure")
                    errors["base"] = "cannot_connect"
                else:
                    normalized = _normalize_devices(devices)
                    if not normalized:
                        errors["base"] = "no_devices"
                    else:
                        await self.async_set_unique_id(
                            f"{app_code}:{user_input[CONF_EMAIL].strip().lower()}"
                        )
                        self._abort_if_unique_id_configured()
                        return self.async_create_entry(
                            title=f"HiSmart Life ({len(normalized)} Geräte)",
                            data={
                                CONF_APP_CODE: app_code,
                                CONF_EMAIL: user_input[CONF_EMAIL].strip(),
                                CONF_REFRESH_TOKEN: client.refresh_token,
                                CONF_DEVICE_DSNS: normalized,
                                CONF_SCAN_INTERVAL: int(DEFAULT_SCAN_INTERVAL.total_seconds()),
                            },
                        )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_APP_CODE, default=DEFAULT_APP_CODE): str,
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): vol.All(str, vol.Length(min=1)),
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            entry = self._reauth_entry
            client = AylaCloudClient(
                async_get_clientsession(self.hass),
                entry.data[CONF_EMAIL],
                HISENSE_EU_APP_ID,
                HISENSE_EU_APP_SECRET,
            )
            try:
                await client.async_login(user_input[CONF_PASSWORD])
                devices = await client.async_list_devices()
            except AylaAuthError as err:
                _LOGGER.warning("HiSmart Life reauthentication was rejected: %s", err)
                errors["base"] = "invalid_auth"
            except (AylaConnectionError, AylaRateLimitError) as err:
                _LOGGER.warning("HiSmart Life cloud could not be reached during reauth: %s", err)
                errors["base"] = "cannot_connect"
            else:
                data = {
                    **entry.data,
                    CONF_REFRESH_TOKEN: client.refresh_token,
                    CONF_DEVICE_DSNS: _normalize_devices(devices),
                }
                self.hass.config_entries.async_update_entry(entry, data=data)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return HisenseOptionsFlow()


class HisenseOptionsFlow(config_entries.OptionsFlow):
    """Adjust cloud polling without repeating login."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, int(DEFAULT_SCAN_INTERVAL.total_seconds())),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                    )
                }
            ),
        )


def _normalize_devices(devices: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    normalized: dict[str, dict[str, str]] = {}
    for device in devices:
        dsn = device.get("dsn")
        if not isinstance(dsn, str) or not dsn:
            continue
        normalized[dsn] = {
            "name": str(device.get("product_name") or device.get("dsn")),
            "product_name": str(device.get("product_name") or "Hisense air conditioner"),
        }
    return normalized
