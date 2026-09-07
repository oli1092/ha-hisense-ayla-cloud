# Testing and troubleshooting

## Read-only test

Run from the repository root with Python 3.12+ and `aiohttp`:

```shell
python -m pip install aiohttp
python scripts/test_cloud.py
```

Alternatively, with uv:

```shell
uv run --no-project --python 3.12 --with aiohttp python scripts/test_cloud.py
```

Enter email at `HiSmart-Life-E-Mail` and password at `Passwort (verdeckt)`.
Never put credentials in command-line arguments or scripts. Expected milestones:
`Login: OK`, discovered devices, property output and
`Token-Refresh und anschließende Cloud-Abfrage: OK` (refresh and subsequent request succeeded).
The expected count of three is a development reference, not an account-size limit.

Unknown property values may be `REDACTED`. Python `None` and JSON `null` mean no
value, not off, zero watts or a cleared error.

## Single-device control test

```shell
python scripts/test_write.py
```

Log in and select a device number. The menu is currently German:

| Selection | Action |
| --- | --- |
| 1 | Turn on |
| 2 | Turn off |
| 3 | Set cooling mode and turn on |
| 4 | Set target temperature, whole degrees from 16–30 °C |
| 5 | Read measurements once per minute for three minutes |
| 0 | Exit, preserving the final device state |

Each write requires `JA` (yes). A suggested sequence is on, cooling, observation,
then off. Check the app after commands. The tool does not restore the original
temperature or automatically turn off on exit; use action 2 or the app.

Readback checks the packed register for up to 15 seconds. A match confirms only
the cloud value. If it does not match, check the app before repeating the command.
A network error after submission can leave execution uncertain.

## Recorded validation for 0.2.0

- Three AEH-W4E1 devices: login, discovery, 45 properties each and token refresh.
- Packed targets of 25/24/24 °C matched the app.
- One target changed from 25 to 26 °C, confirmed by cloud and app.
- Power on/off and a cooling command were accepted and read back on one device.
- Indoor temperature changed from 29 to 27 °C over the operating test.
- Humidity, voltage, power display and electricity stayed null through two
  three-minute observations. This does not prove permanent lack of support.
- Other modes, actual transitions between different modes and other controls remain unverified.

## Home Assistant validation still required

Verify entity creation, initial state, service calls, options changes, restart
persistence and reauthentication. Test cloud failures and stale/offline device
data. Standalone success does not establish a correct HA lifecycle.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| uv or Python not found | Use a full executable path; use uv `--python` with an installed interpreter, or repair Python. This is not an Ayla login error. |
| HACS GitHub 404 | Repository URL and visibility; test signed-out access. Authenticated git push does not establish public download access. |
| Integration absent | Folder placement, restart completion and HA loader logs. |
| Login rejected | Correct HiSmart Life account, EU code and installed version. Version 0.2.0 fixes the wrong application-secret prefix in 0.1.0. |
| No devices | Devices must be paired and visible in the same vendor-app account. |
| Old on/off state after a write | Allow another poll; standalone properties may lag behind the packed register. |
| Missing measurements | Compare during operation; do not replace null with zero or guess units. |
| Rate limit or unavailable | Keep polling at 60 seconds or slower and avoid repeated command tests. |

Download diagnostics from the integration's HA menu after successful setup.
Review the output before sharing; include versions and hardware, not account secrets.
