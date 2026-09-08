# Hisense Ayla Cloud

A cloud-only Home Assistant custom integration for Hisense air conditioners with
AEH-W4E1 / AEH-W4B1 Wi-Fi modules using the **HiSmart Life EU** account service.

Home Assistant and the air conditioners do not need to share a network. All
control and status requests use the Ayla cloud: no local HTTP callback, callback
port, LAN-key exchange, or connection to device IP addresses is required.

**Experimental — version 0.3.0.** Basic climate entities have been loaded in Home
Assistant. Additional controls in this version are reference-based and need device
validation. This unofficial project is not affiliated with Hisense or Ayla.

## AI development disclosure

This repository, including its code and documentation, was created with substantial
assistance from AI (OpenAI Codex), guided by the project owner. AI-generated code
can contain errors, and passing automated tests does not establish production
reliability. Validation is limited to the tests and device observations documented
here; do not assume a comprehensive human code review or independent audit.
Review and test the integration in your own environment before relying on it for
unattended climate control.

## Compatibility

| Item | Status |
| --- | --- |
| AEH-W4E1 | Discovery and property reads tested with three devices |
| AEH-W4B1 | Intended target; not separately hardware-tested |
| Account / region | HiSmart Life, `hisense-eu` only |
| Other regions or Hisense apps | Not supported in this version |
| Standalone tools | Python 3.12+ and `aiohttp`; no Home Assistant required |
| Home Assistant | Current config-entry/coordinator APIs; minimum supported Core version not yet established |

Devices must already be paired and visible in the HiSmart Life account. Both
devices and Home Assistant need internet access.

The separate domain `hisense_ayla_cloud` does not replace or modify
`hisense_aircon`. Both integrations can remain installed. Avoid conflicting
automations controlling the same device through both integrations.

## Features and validation

Each device has a climate entity, indoor-temperature sensor, power binary sensor
and raw diagnostic entities for its cloud properties. Extra controls are marked
experimental and are created only when the corresponding direct property or
packed register is present. No additional polling is needed for these entities.

| Feature | Current status |
| --- | --- |
| Login and token refresh | Tested against the live EU cloud |
| Discovery and property reads | Three devices, 45 properties each |
| Indoor temperature | Read from `f_temp_in` |
| Target temperature | Packed value decoded; 24/25/26 °C confirmed against the app |
| Set temperature | Whole-degree Celsius, 16–30 °C; cloud write and app confirmation tested |
| Turn on / off | Cloud submission and readback tested on one device |
| HVAC modes | All reference modes available experimentally for packed-register devices; only cooling tested |
| Cooling command | Accepted and read back while already in cooling mode; transition from another mode not tested |
| Polling | Default 60 seconds; configurable from 30 to 3,600 seconds |
| Failure handling | Backoff, availability and reauth implemented; HA runtime validation pending |
| Diagnostics | Identifiers redacted and property values conservatively filtered |

Experimental controls include fan speed, Eco, Quiet, Turbo and vertical/horizontal
swing. Backlight and 8-degree heating require their own cloud properties. Sleep
and swing-angle selects appear if their properties exist, but commands are refused
when cloud metadata marks them read-only (including Sleep on the tested devices).
Backlight uses the reference's inverted polarity. Validate one control at a time.

All received boolean properties have raw binary-sensor representations; other
properties have raw sensors. Null values stay unknown, and raw measurements do
not claim unverified units or energy statistics. Arbitrary string/object values
remain unknown except the version string. Raw error flags do not infer fault polarity.

## HACS installation

The repository must be accessible to HACS. This is a custom repository; it is
not a claim of inclusion in the default HACS catalog.

1. Open HACS and choose **Custom repositories** from the three-dot menu.
2. Add `https://github.com/oli1092/HiSmartLife-HA-Integration`, type **Integration**.
3. Find **Hisense Ayla Cloud** and download it.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration** and select **Hisense Ayla Cloud**.
6. Enter `hisense-eu`, your HiSmart Life email and password.

See the official [HACS instructions](https://www.hacs.xyz/docs/faq/custom_repositories/).

For manual installation, copy `custom_components/hisense_ayla_cloud` into your
Home Assistant configuration's `custom_components` directory. The final manifest
path must be `<config>/custom_components/hisense_ayla_cloud/manifest.json`.
Restart and follow steps 5–6 above.

Use the integration's options to adjust polling. Keep the 60-second default
unless necessary: three devices normally require three property requests per
poll, plus authentication and command requests.

## Test without Home Assistant

In an interactive terminal with Python 3.12+:

```shell
git clone https://github.com/oli1092/HiSmartLife-HA-Integration.git
cd HiSmartLife-HA-Integration
python -m pip install aiohttp
python scripts/test_cloud.py
```

This uses the same API client as the integration. It logs in, discovers devices,
reads properties and tests token refresh without controlling any device.
Password input is hidden; credentials and tokens are not saved by these tools.
The current terminal prompts are German; an English walkthrough is in the
[testing guide](docs/TESTING.md).

For an explicit single-device control test, run `python scripts/test_write.py`.
It asks for a device, action and confirmation before each write. It can turn
the air conditioner on, and changed settings remain in effect after the test.

## Known limitations

- Cloud acceptance or matching readback alone does not prove physical execution.
  Check the app and, where possible, the device.
- Separate status properties can lag behind the packed register. A brief old
  on/off state after a command is possible; HA state is not updated optimistically.
- Humidity, voltage, power display and electricity remained `null` during two
  three-minute operating observations. Null means no value, not zero. Units,
  scaling and reporting behavior for these measurements are unverified.
- Packed Fahrenheit temperature writes are not supported.
- Discovery occurs during setup/reauthentication, not continuously.
- Device-offline detection, stale cloud values and concurrent app/HA control need
  further validation. The unofficial cloud API may change without notice.

## Privacy

Credentials are sent over HTTPS to the Ayla EU account service. Home Assistant
stores the account email, refresh token and device metadata in its config entry;
the password is not retained by this integration. Access tokens remain in memory,
and rotated refresh tokens are saved for later restarts.

The integration contacts `user-field-eu.aylanetworks.com` and
`ads-eu.aylanetworks.com`. Device telemetry and commands pass through the vendor's
cloud. There is no local-control or offline fallback.

Diagnostics omit device DSNs and names and redact unrecognized property values.
Review output before sharing: property names and operating values remain visible.
Never post credentials, tokens, full config-entry data or unreviewed logs.

## Documentation and feedback

- [Testing and troubleshooting](docs/TESTING.md)
- [Cloud properties and verified mapping](docs/PROPERTIES.md)
- [Development and roadmap](docs/DEVELOPMENT.md)

When reporting an issue, include the integration and HA versions, module model,
region, expected behavior and sanitized diagnostics. State whether the standalone
cloud test succeeds.

## References

- [wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon): HiSmart login and packed Hisense fields.
- [rewardone/ayla-iot-unofficial](https://github.com/rewardone/ayla-iot-unofficial): Ayla API reference.
- [sk7n4k3d/delonghi-ha](https://github.com/sk7n4k3d/delonghi-ha): Cloud datapoint writes.
