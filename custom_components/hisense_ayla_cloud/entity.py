"""Shared coordinator-backed read-only entity."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HisenseCoordinator
from .api import AylaError
from homeassistant.exceptions import HomeAssistantError


class HisenseReadEntity(CoordinatorEntity[HisenseCoordinator]):
    """Share device identity and availability without extra cloud requests."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, dsn, suffix):
        super().__init__(coordinator)
        self._dsn = dsn
        self._attr_unique_id = f"{dsn}_{suffix}"
        info = coordinator.device_info[dsn]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, dsn)},
            "name": info.get("name", dsn),
            "manufacturer": "Hisense",
            "model": info.get("product_name", "Hisense air conditioner"),
        }

    @property
    def snapshot(self):
        return (self.coordinator.data or {}).get(self._dsn)

    @property
    def available(self):
        return bool(self.coordinator.last_update_success and self.snapshot and self.snapshot.available)

    async def async_command(self, command, value):
        try:
            await self.coordinator.client.async_command(self._dsn, command, value)
        except (AylaError, ValueError) as err:
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()
