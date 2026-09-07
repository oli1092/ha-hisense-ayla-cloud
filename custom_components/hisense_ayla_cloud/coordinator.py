"""Coordinator for cloud polling and per-device availability."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AylaAuthError, AylaCloudClient, AylaConnectionError, AylaRateLimitError
from .const import DEFAULT_SCAN_INTERVAL
from .models import DeviceSnapshot

_LOGGER = logging.getLogger(__name__)


class HisenseCoordinator(DataUpdateCoordinator[dict[str, DeviceSnapshot]]):
    """Poll all configured devices through the Ayla cloud."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: AylaCloudClient,
        device_info: dict[str, dict[str, Any]],
        scan_interval: timedelta = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Hisense Ayla Cloud",
            config_entry=entry,
            update_interval=scan_interval,
            always_update=False,
        )
        self.client = client
        self.device_info = device_info
        self._base_scan_interval = scan_interval
        self._failure_count = 0
        self._last_data: dict[str, DeviceSnapshot] = {}
        self._failure_logged = False

    async def _async_update_data(self) -> dict[str, DeviceSnapshot]:
        """Fetch every device, retaining data only from successful responses."""

        result: dict[str, DeviceSnapshot] = {}
        failures = 0
        for dsn, info in self.device_info.items():
            try:
                properties = await self.client.async_get_properties(dsn)
            except AylaAuthError as err:
                raise ConfigEntryAuthFailed("Ayla authentication expired") from err
            except AylaRateLimitError as err:
                raise UpdateFailed("Ayla rate limit", retry_after=err.retry_after or 60) from err
            except AylaConnectionError as err:
                failures += 1
                previous = self._last_data.get(dsn)
                result[dsn] = DeviceSnapshot(
                    dsn,
                    info.get("name", dsn),
                    info.get("product_name", "Hisense air conditioner"),
                    previous.properties if previous else {},
                    available=False,
                    error="cloud_unavailable",
                )
                continue
            result[dsn] = DeviceSnapshot(
                dsn,
                info.get("name", dsn),
                info.get("product_name", "Hisense air conditioner"),
                properties,
                available=True,
            )

        if failures == len(self.device_info):
            self._failure_count = min(self._failure_count + 1, 7)
            self.update_interval = min(
                self._base_scan_interval * (2**self._failure_count),
                timedelta(hours=1),
            )
            if not self._failure_logged:
                _LOGGER.warning("Hisense Ayla cloud is unavailable")
                self._failure_logged = True
            raise UpdateFailed("All Hisense devices are unavailable")
        if failures:
            self._failure_count = min(self._failure_count + 1, 7)
            self.update_interval = min(
                self._base_scan_interval * (2**self._failure_count),
                timedelta(hours=1),
            )
            if not self._failure_logged:
                _LOGGER.warning("Some Hisense Ayla devices are unavailable")
                self._failure_logged = True
        else:
            self._failure_count = 0
            self.update_interval = self._base_scan_interval
            self._failure_logged = False
        self._last_data = result
        return result
