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
    if client.refresh_token and client.refresh_token != refresh_token:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_REFRESH_TOKEN: client.refresh_token}
        )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry) -> bool:
    """Unload the integration cleanly."""

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unloaded
