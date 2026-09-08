"""Experimental fan and directly advertised Sleep/angle controls."""

from homeassistant.components.select import SelectEntity
from .entity import HisenseReadEntity
from .experimental import FAN_MODES, DIRECT_OPTIONS, packed_value, has_packed


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    entities = []
    for dsn in coordinator.device_info:
        snapshot = (coordinator.data or {}).get(dsn)
        if has_packed(snapshot):
            entities.append(HisenseSelect(coordinator, dsn, "fan", FAN_MODES))
        for key in ("t_sleep", "t_swing_angle"):
            if snapshot and key in snapshot.properties:
                entities.append(HisenseSelect(coordinator, dsn, key, DIRECT_OPTIONS[key]))
    async_add_entities(entities)


class HisenseSelect(HisenseReadEntity, SelectEntity):
    def __init__(self, coordinator, dsn, key, options):
        super().__init__(coordinator, dsn, key)
        self.key, self.mapping = key, options
        self._attr_name = f"{key.removeprefix('t_').replace('_', ' ').title()} (experimental)"
        self._attr_options = list(options)

    @property
    def current_option(self):
        value = packed_value(self.snapshot, "fan") if self.key == "fan" else self.snapshot.value(self.key) if self.snapshot else None
        return next((name for name, raw in self.mapping.items() if type(value) is int and raw == value), None)

    @property
    def extra_state_attributes(self):
        prop = "t_control_value" if self.key == "fan" else self.key
        return {"cloud_read_only": self.snapshot.property(prop).get("read_only") if self.snapshot else None}

    async def async_select_option(self, option):
        await self.async_command(self.key, option)
