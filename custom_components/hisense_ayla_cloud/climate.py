"""Climate entities with verified reads and experimental cloud commands."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    PROPERTY_HUMIDITY,
    PROPERTY_POWER,
    PROPERTY_TARGET_TEMP,
    PROPERTY_TEMP_IN,
    PROPERTY_WORK_MODE,
)
from .coordinator import HisenseCoordinator
from .models import DeviceSnapshot, climate_hvac_mode, climate_modes, target_temperature
from .api import AylaError


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Create one climate entity per discovered device."""

    coordinator: HisenseCoordinator = entry.runtime_data
    async_add_entities(
        HisenseCloudClimate(coordinator, dsn) for dsn in coordinator.device_info
    )


class HisenseCloudClimate(CoordinatorEntity[HisenseCoordinator], ClimateEntity):
    """Read cloud state; never optimistically apply submitted commands."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature(0)
    _attr_min_temp = 16
    _attr_max_temp = 30
    _attr_target_temperature_step = 1

    @property
    def supported_features(self):
        snapshot = self._snapshot
        if snapshot and snapshot.property("t_control_value").get("read_only") is False:
            return (ClimateEntityFeature.TARGET_TEMPERATURE |
                    ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF)
        return ClimateEntityFeature(0)

    async def _command(self, command, value):
        try:
            await self.coordinator.client.async_command(self._dsn, command, value)
        except (AylaError, ValueError) as err:
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self):
        await self._command("power", True)

    async def async_turn_off(self):
        await self._command("power", False)

    async def async_set_temperature(self, **kwargs):
        await self._command("temperature", kwargs[ATTR_TEMPERATURE])

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == "off":
            await self.async_turn_off()
        else:
            await self._command("mode", hvac_mode)

    def __init__(self, coordinator: HisenseCoordinator, dsn: str) -> None:
        super().__init__(coordinator)
        self._dsn = dsn
        info = coordinator.device_info[dsn]
        self._attr_unique_id = f"{dsn}_climate"
        self._attr_name = "Climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, dsn)},
            "name": info.get("name", dsn),
            "manufacturer": "Hisense",
            "model": info.get("product_name", "Hisense air conditioner"),
        }

    @property
    def _snapshot(self) -> DeviceSnapshot | None:
        return self.coordinator.data.get(self._dsn) if self.coordinator.data else None

    @property
    def available(self) -> bool:
        snapshot = self._snapshot
        return bool(snapshot and snapshot.available and self.coordinator.last_update_success)

    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def current_temperature(self) -> float | None:
        return _number(self._snapshot, PROPERTY_TEMP_IN)

    @property
    def target_temperature(self) -> float | None:
        return target_temperature(self._snapshot) if self._snapshot else None

    @property
    def hvac_mode(self) -> str | None:
        return climate_hvac_mode(self._snapshot) if self._snapshot else None

    @property
    def hvac_modes(self) -> list[str]:
        return climate_modes(self._snapshot) if self._snapshot else []

    @property
    def current_humidity(self) -> int | None:
        value = _number(self._snapshot, PROPERTY_HUMIDITY)
        return int(value) if value is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        snapshot = self._snapshot
        if not snapshot:
            return {}
        return {
            "cloud_writes_experimental": True,
            "cloud_property_count": len(snapshot.properties),
            "power_property": PROPERTY_POWER if PROPERTY_POWER in snapshot.properties else None,
            "work_mode_property": (
                PROPERTY_WORK_MODE if PROPERTY_WORK_MODE in snapshot.properties else None
            ),
        }


def _number(snapshot: DeviceSnapshot | None, name: str) -> float | None:
    if not snapshot:
        return None
    value = snapshot.value(name)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
