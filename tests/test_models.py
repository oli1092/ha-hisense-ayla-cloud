"""Pure mapping tests for the read-only prototype."""

from hisense_ayla_cloud.models import (
    DeviceSnapshot,
    climate_hvac_mode,
    climate_modes,
)
import pytest


@pytest.mark.parametrize("power", [0, False, "0", "OFF"])
def test_actual_cloud_power_off(power):
    snapshot = DeviceSnapshot("test", "test", "test", {
        "t_power": {"value": power}, "t_work_mode": {"value": 2},
        "f_temp_in": {"value": 29.0},
    })
    assert climate_hvac_mode(snapshot) == "off"


def test_numeric_mode_from_reference():
    snapshot = DeviceSnapshot("test", "test", "test", {
        "t_power": {"value": 1}, "t_work_mode": {"value": 2},
    })
    assert climate_hvac_mode(snapshot) == "cool"
    assert climate_modes(snapshot) == ["off", "cool"]


def test_unknown_numeric_mode_not_guessed():
    snapshot = DeviceSnapshot("test", "test", "test", {
        "t_power": {"value": 1}, "t_work_mode": {"value": 99},
    })
    assert climate_hvac_mode(snapshot) is None


def test_hisense_properties_map_to_climate() -> None:
    snapshot = DeviceSnapshot(
        "dsn-1",
        "Living room",
        "AEH-W4E1",
        {
            "t_power": {"name": "t_power", "value": "ON"},
            "t_work_mode": {
                "name": "t_work_mode",
                "value": "COOL",
                "possible_values": ["AUTO", "COOL", "HEAT"],
            },
            "t_temp": {"name": "t_temp", "value": 22},
            "f_temp_in": {"name": "f_temp_in", "value": 24.5},
        },
        available=True,
    )
    assert climate_hvac_mode(snapshot) == "cool"
    assert climate_modes(snapshot) == ["off", "auto", "cool", "heat"]


def test_power_off_overrides_work_mode() -> None:
    snapshot = DeviceSnapshot(
        "dsn-1",
        "Living room",
        "AEH-W4E1",
        {
            "t_power": {"value": "OFF"},
            "t_work_mode": {"value": "COOL"},
        },
        available=True,
    )
    assert climate_hvac_mode(snapshot) == "off"
