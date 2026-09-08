"""Reported power state, not compressor activity or cloud connectivity."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .entity import HisenseReadEntity
from .models import power_state
from homeassistant.const import EntityCategory


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities(HisensePower(coordinator, dsn, "power")
                       for dsn in coordinator.device_info)
    async_add_entities(HisenseRawBinary(coordinator, dsn, name)
        for dsn, snapshot in (coordinator.data or {}).items()
        for name, prop in snapshot.properties.items()
        if name != "t_power" and prop.get("base_type") == "boolean")


class HisensePower(HisenseReadEntity, BinarySensorEntity):
    _attr_translation_key = "power"
    _attr_device_class = BinarySensorDeviceClass.POWER

    @property
    def is_on(self):
        return power_state(self.snapshot) if self.snapshot else None


class HisenseRawBinary(HisenseReadEntity, BinarySensorEntity):
    """Raw flags: no inferred polarity, problem classification or default false."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, dsn, name):
        super().__init__(coordinator, dsn, f"raw_{name}")
        self.key = name
        self._attr_name = f"{name} (raw)"

    @property
    def is_on(self):
        value = self.snapshot.value(self.key) if self.snapshot else None
        return bool(value) if type(value) in (int, bool) and value in (0, 1) else None
