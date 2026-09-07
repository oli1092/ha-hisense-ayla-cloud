# Hisense Ayla Cloud

Cloud-only Home Assistant custom integration prototype for Hisense air conditioners
with AEH-W4E1/W4B1 modules and the HiSmart Life EU app.

## Current scope

This first milestone implements:

- HiSmart Life/Ayla login and refresh-token handling
- automatic cloud discovery
- cloud property polling (default 60 seconds)
- redacted diagnostics containing raw property metadata
- a `climate` entity mapping power, mode, target temperature, indoor temperature and humidity
- experimental cloud commands for power, Celsius temperature (16–30), and observed/advertised HVAC modes

It deliberately does **not** use local callbacks, LAN keys, local IP addresses or
device-local HTTP. Login, discovery, refresh and packed temperatures have been
verified against three real devices. Temperature writes were confirmed by cloud
readback and the HiSmart-Life app. Power on/off and a cooling-mode command were
accepted and read back in a live test on one device. Changing from another mode
to cooling has not yet been tested. Only observed/advertised modes are offered
(currently off/cool); other modes and fan/swing controls remain pending.
Commands read the latest register first and never optimistically update HA state.
Ambiguous network failures are not automatically retried.

In the live test, humidity, voltage (`f_votage`), power display and electricity
properties remained null throughout two three-minute operating observations.
Null is not interpreted as zero. Indoor temperature updated from 29 to 27 °C.
The separate power property can lag behind the packed control value; HA displays
the reported state and does not assume a submitted command has executed.

For a deliberate single-device temperature test, run `python scripts/test_write.py`
in an interactive terminal with aiohttp installed. It prompts for credentials,
device number, temperature and explicit confirmation, then checks the cloud
readback. Check the HiSmart-Life app as well: a cloud response alone does not
prove physical execution. The selected temperature remains set after the test.

## Installation

Install this repository as a HACS custom repository, restart Home Assistant, and
add **Hisense Ayla Cloud** under Settings → Devices & services. Use app code
`hisense-eu` and the same HiSmart Life credentials as the mobile app.

## Standalone read-only cloud test

With Python 3.12+ and `aiohttp`, run `python scripts/test_cloud.py` from this
repository in an interactive terminal. With uv, use
`uv run --no-project --with aiohttp python scripts/test_cloud.py`.
The test prompts for email and a hidden password; never pass credentials as
command-line arguments. It uses the integration's API client to log in, discover
devices, read properties, and refresh the token. It does not write device values
or save credentials/tokens. Device identifiers are omitted; unknown property
values are redacted conservatively. This can hide enum values that need later
verification. A successful probe validates cloud access, not HA setup itself.

## Privacy and limitations

Credentials and tokens are never logged. Diagnostics redact account identifiers,
tokens and device DSNs. The integration requires outbound HTTPS access to the
Ayla EU cloud; cloud outages make entities unavailable. The cloud API is
unofficial and may change without notice.
