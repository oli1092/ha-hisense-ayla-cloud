"""Conservative packed commands based on the Hisense reference register."""

from .models import DeviceSnapshot, climate_modes, NUMERIC_HVAC_MODES


def build_command(properties, command, value):
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
        if value == "off" or value not in climate_modes(snapshot):
            raise ValueError("Mode not observed or advertised by this device")
        raw = next((key for key, mode in NUMERIC_HVAC_MODES.items() if mode == value), None)
        if raw is None:
            raise ValueError("Unsupported mode")
        control = (control & ~(15 << 8)) | (((raw << 1) | 1) << 8)
        control = (control & ~(3 << 5)) | (3 << 5)
    else:
        raise ValueError("Unknown command")
    return "t_control_value", control
