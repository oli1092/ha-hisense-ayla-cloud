"""Verified cloud samples and packed writes without contacting devices."""

import pytest
from hisense_ayla_cloud.commands import build_command
from hisense_ayla_cloud.models import DeviceSnapshot, target_temperature


def properties(control=3343616):
    return {"t_control_value": {"value": control, "read_only": False},
            "t_power": {"value": 0}, "t_work_mode": {"value": 2}}


@pytest.mark.parametrize("control, expected", [(3343616, 25), (3212544, 24)])
def test_user_verified_temperatures(control, expected):
    assert target_temperature(DeviceSnapshot("", "", "", properties(control))) == expected


def test_temperature_preserves_other_settings():
    name, encoded = build_command(properties(), "temperature", 24)
    assert name == "t_control_value"
    assert encoded == 3212288  # The previous mode-change flag (bit 8) is cleared.
    assert (encoded >> 6) & 1 == 0
    assert (encoded >> 9) & 7 == 2


@pytest.mark.parametrize("enabled", [True, False])
def test_power_preserves_temperature_and_mode(enabled):
    _, encoded = build_command(properties(), "power", enabled)
    assert (encoded >> 6) & 1 == int(enabled)
    assert encoded & (1 << 5)
    assert (encoded >> 17) & 63 == 25
    assert (encoded >> 9) & 7 == 2


def test_cooling_sets_mode_and_power_in_one_command():
    _, encoded = build_command(properties(), "mode", "cool")
    assert (encoded >> 6) & 1 == 1
    assert (encoded >> 9) & 7 == 2
    assert (encoded >> 17) & 63 == 25


@pytest.mark.parametrize("value", [15, 31, 24.5, None, float("nan")])
def test_invalid_temperature_rejected(value):
    with pytest.raises(ValueError):
        build_command(properties(), "temperature", value)


def test_unobserved_mode_rejected():
    with pytest.raises(ValueError):
        build_command(properties(), "mode", "heat")
