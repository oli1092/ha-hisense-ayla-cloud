"""Missing cloud values must never become false or zero measurements."""

import pytest
from hisense_ayla_cloud.models import DeviceSnapshot, indoor_temperature, power_state


@pytest.mark.parametrize("raw,expected", [(0, False), (1, True), (False, False),
    (True, True), (None, None), (2, None), ("OFF", False), ("ON", True)])
def test_reported_power(raw, expected):
    snapshot = DeviceSnapshot("", "", "", {"t_power": {"value": raw}})
    assert power_state(snapshot) is expected


@pytest.mark.parametrize("raw,expected", [(29.0, 29.0), (0, 0.0), (None, None),
    (True, None), (float("nan"), None), (float("inf"), None)])
def test_indoor_measurement(raw, expected):
    snapshot = DeviceSnapshot("", "", "", {"f_temp_in": {"value": raw}})
    assert indoor_temperature(snapshot) == expected
