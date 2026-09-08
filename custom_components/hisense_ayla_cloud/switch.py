"""Experimental switches; writing always checks fresh cloud metadata."""

from homeassistant.components.switch import SwitchEntity
from .entity import HisenseReadEntity
from .experimental import packed_value, has_packed, DIRECT_OPTIONS


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    entities = []
    for dsn in coordinator.device_info:
        snapshot = (coordinator.data or {}).get(dsn)
        if has_packed(snapshot):
            for key in ("eco", "quiet", "turbo", "vertical_swing", "horizontal_swing"):
                entities.append(HisenseSwitch(coordinator, dsn, key))
        for key in ("t_backlight", "t_temp_eight"):
            if snapshot and key in snapshot.properties:
                entities.append(HisenseSwitch(coordinator, dsn, key))
    async_add_entities(entities)


class HisenseSwitch(HisenseReadEntity, SwitchEntity):
    def __init__(self, coordinator, dsn, key):
        super().__init__(coordinator, dsn, key)
        self.key = key
        label = {"t_backlight": "Backlight", "t_temp_eight": "8 degree heating"}.get(key, key.replace("_", " ").title())
        self._attr_name = f"{label} (experimental)"

    @property
    def is_on(self):
        if self.key in DIRECT_OPTIONS:
            value = self.snapshot.value(self.key) if self.snapshot else None
            if type(value) not in (int, bool) or value not in (0, 1):
                return None
            return value == DIRECT_OPTIONS[self.key]["on"]
        value = packed_value(self.snapshot, self.key)
        return bool(value) if value is not None else None

    async def async_turn_on(self, **kwargs):
        await self.async_command(self.key, "on" if self.key in DIRECT_OPTIONS else True)

    async def async_turn_off(self, **kwargs):
        await self.async_command(self.key, "off" if self.key in DIRECT_OPTIONS else False)
