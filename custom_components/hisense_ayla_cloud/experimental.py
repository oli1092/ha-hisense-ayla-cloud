"""Unverified device capabilities taken from the Hisense reference implementation."""

# Name -> (value bit offset, value width). The preceding bit is a change flag.
PACKED_FIELDS = {"fan": (1, 4), "turbo": (13, 1), "eco": (15, 1),
                 "vertical_swing": (25, 1), "horizontal_swing": (27, 1), "quiet": (29, 1)}
FAN_MODES = {"auto": 0, "lower": 5, "low": 6, "medium": 7, "high": 8, "higher": 9}
DIRECT_OPTIONS = {
    "t_backlight": {"on": 0, "off": 1},  # Reference Dimmer enum is inverted.
    "t_temp_eight": {"on": 1, "off": 0},
    "t_sleep": {"stop": 0, "1": 1, "2": 2, "3": 3, "4": 4},
    "t_swing_angle": {"sweep": 0, "auto": 1, **{f"angle_{i}": i + 1 for i in range(1, 7)}},
}


def packed_value(snapshot, name):
    if snapshot is None:
        return None
    raw = snapshot.value("t_control_value")
    if type(raw) is not int or not 0 <= raw <= 0xFFFFFFFF:
        return None
    offset, width = PACKED_FIELDS[name]
    return (raw >> offset) & ((1 << width) - 1)


def has_packed(snapshot):
    return snapshot is not None and "t_control_value" in snapshot.properties
