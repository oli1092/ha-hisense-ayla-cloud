"""Verified indoor-temperature measurement."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfTemperature

from .entity import HisenseReadEntity
from .models import indoor_temperature
from math import isfinite
from homeassistant.const import EntityCategory


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities(HisenseIndoorTemperature(coordinator, dsn, "indoor_temperature")
                       for dsn in coordinator.device_info)
    async_add_entities(HisenseRawSensor(coordinator, dsn, name)
        for dsn, snapshot in (coordinator.data or {}).items()
        for name, prop in snapshot.properties.items()
        if name != "f_temp_in" and prop.get("base_type") != "boolean")


class HisenseIndoorTemperature(HisenseReadEntity, SensorEntity):
    _attr_translation_key = "indoor_temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        return indoor_temperature(self.snapshot) if self.snapshot else None


class HisenseRawSensor(HisenseReadEntity, SensorEntity):
    """All non-boolean properties, without guessing units or string semantics."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, dsn, name):
        super().__init__(coordinator, dsn, f"raw_{name}")
        self.key = name
        self._attr_name = f"{name} (raw)"

    @property
    def native_value(self):
        value = self.snapshot.value(self.key) if self.snapshot else None
        if type(value) in (int, float) and isfinite(value):
            return value
        if self.key == "version" and isinstance(value, str) and len(value) <= 64:
            return value
        return None

    @property
    def extra_state_attributes(self):
        prop = self.snapshot.property(self.key) if self.snapshot else {}
        return {"cloud_read_only": prop.get("read_only"), "cloud_base_type": prop.get("base_type")}
