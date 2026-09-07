"""Hisense Ayla cloud-only Home Assistant integration."""

from __future__ import annotations

PLATFORMS = ["climate"]


async def async_setup_entry(hass, entry) -> bool:
    """Set up a cloud account and its read-only entities."""

    from datetime import timedelta

    from homeassistant.exceptions import ConfigEntryAuthFailed
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .api import AylaCloudClient
    from .const import (
        CONF_DEVICE_DSNS,
        CONF_EMAIL,
        CONF_REFRESH_TOKEN,
        CONF_SCAN_INTERVAL,
        HISENSE_EU_APP_ID,
        HISENSE_EU_APP_SECRET,
    )
    from .coordinator import HisenseCoordinator

    client = AylaCloudClient(
        async_get_clientsession(hass),
        entry.data[CONF_EMAIL],
        HISENSE_EU_APP_ID,
        HISENSE_EU_APP_SECRET,
    )
    refresh_token = entry.data.get(CONF_REFRESH_TOKEN)
    if not refresh_token:
        raise ConfigEntryAuthFailed("Missing Ayla refresh token")
    client.restore_refresh_token(refresh_token)

    def persist_token(token):
        if token != entry.data.get(CONF_REFRESH_TOKEN):
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_REFRESH_TOKEN: token}
            )

    client.on_token_change = persist_token
    interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, 60),
    )
    coordinator = HisenseCoordinator(
        hass,
        entry,
        client,
        entry.data.get(CONF_DEVICE_DSNS, {}),
        scan_interval=timedelta(seconds=int(interval)),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    previous_options = dict(entry.options)

    async def update_options(hass, updated_entry):
        nonlocal previous_options
        if dict(updated_entry.options) == previous_options:
            return
        previous_options = dict(updated_entry.options)
        coordinator.update_interval = timedelta(
            seconds=int(updated_entry.options.get(CONF_SCAN_INTERVAL, 60))
        )
        coordinator._base_scan_interval = coordinator.update_interval
        await coordinator.async_request_refresh()

    entry.async_on_unload(entry.add_update_listener(update_options))
    return True


async def async_unload_entry(hass, entry) -> bool:
    """Unload the integration cleanly."""

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unloaded
