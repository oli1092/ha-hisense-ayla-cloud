"""Constants for the Hisense Ayla cloud integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "hisense_ayla_cloud"
NAME = "Hisense Ayla Cloud"
DEFAULT_APP_CODE = "hisense-eu"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 3600
CONF_APP_CODE = "app_code"
CONF_EMAIL = "email"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_DEVICE_DSNS = "device_dsns"
CONF_SCAN_INTERVAL = "scan_interval"

EU_USER_SERVER = "user-field-eu.aylanetworks.com"
EU_DEVICES_SERVER = "ads-eu.aylanetworks.com"

# These are the public application identifiers used by HiSmart Life. They are
# required to address the Ayla API, but are never logged or exposed in
# diagnostics. User passwords and cloud tokens are never stored here.
HISENSE_EU_APP_ID = "Hisense-mw-id"
HISENSE_EU_APP_SECRET = "Hisense-wO1LLP8rWPr2cIeqvFaI-0m0z60"

PROPERTY_POWER = "t_power"
PROPERTY_TARGET_TEMP = "t_temp"
PROPERTY_WORK_MODE = "t_work_mode"
PROPERTY_FAN_SPEED = "t_fan_speed"
PROPERTY_FAN_LEFTRIGHT = "t_fan_leftright"
PROPERTY_FAN_POWER = "t_fan_power"
PROPERTY_TEMP_IN = "f_temp_in"
PROPERTY_HUMIDITY = "f_humidity"

HVAC_MODE_MAP = {
    "AUTO": "auto",
    "COOL": "cool",
    "HEAT": "heat",
    "DRY": "dry",
    "FAN": "fan_only",
}

REDACTED = "REDACTED"
