"""Conservative packed commands based on the Hisense reference register."""

from .models import DeviceSnapshot, climate_modes, NUMERIC_HVAC_MODES
from .experimental import PACKED_FIELDS, FAN_MODES, DIRECT_OPTIONS


def build_command(properties, command, value):
    if command in DIRECT_OPTIONS:
        prop = properties.get(command, {})
        if prop.get("read_only") is not False or value not in DIRECT_OPTIONS[command]:
            raise ValueError("Property is read-only, absent or the option is invalid")
        return command, DIRECT_OPTIONS[command][value]
    prop = properties.get("t_control_value", {})
    control = prop.get("value")
    if prop.get("read_only") is not False or type(control) is not int:
        raise ValueError("No writable packed control property")
    if not 0 <= control <= 0xFFFFFFFF:
        raise ValueError("Invalid packed control value")
    control &= 2868817502  # Clear old change flags, preserving setting bits.
    if command == "temperature":
        if type(value) not in (int, float) or not 16 <= value <= 30 or int(value) != value:
            raise ValueError("Temperature must be a whole degree between 16 and 30")
        if control & (1 << 31):
            raise ValueError("Fahrenheit control is not verified")
        control = (control & ~(127 << 16)) | (((int(value) << 1) | 1) << 16)
    elif command == "power":
        if type(value) is not bool:
            raise ValueError("Power must be boolean")
        control = (control & ~(3 << 5)) | (((int(value) << 1) | 1) << 5)
    elif command == "mode":
        snapshot = DeviceSnapshot("", "", "", properties)
        if value == "off" or value not in NUMERIC_HVAC_MODES.values():
            raise ValueError("Mode not observed or advertised by this device")
        raw = next((key for key, mode in NUMERIC_HVAC_MODES.items() if mode == value), None)
        if raw is None:
            raise ValueError("Unsupported mode")
        control = (control & ~(15 << 8)) | (((raw << 1) | 1) << 8)
        control = (control & ~(3 << 5)) | (3 << 5)
    elif command in PACKED_FIELDS:
        offset, width = PACKED_FIELDS[command]
        if command == "fan":
            if value not in FAN_MODES:
                raise ValueError("Unsupported fan speed")
            raw = FAN_MODES[value]
        else:
            if type(value) is not bool:
                raise ValueError("Switch value must be boolean")
            raw = int(value)
        mask = ((1 << (width + 1)) - 1) << (offset - 1)
        control = (control & ~mask) | (raw << offset) | (1 << (offset - 1))
    else:
        raise ValueError("Unknown command")
    return "t_control_value", control
