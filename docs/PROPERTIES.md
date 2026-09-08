# Cloud properties and mapping

Each tested device exposes 45 Ayla properties. Presence does not establish a
current value or support for a control. `read_only: false` is cloud metadata,
not proof that the device executes a command.

| Property | Cloud type | Observation |
| --- | --- | --- |
| `t_power` | boolean | Numeric 0/1; status can lag after writing |
| `t_work_mode` | integer | 2 observed, mapped to cooling |
| `t_control_value` | integer | Writable packed register used for tested commands |
| `f_temp_in` | decimal | Indoor temperature, plausible Celsius readings |
| `t_sleep` | integer | 0 observed, read-only metadata; no select implemented |
| `t_backlight` | boolean | Writable metadata, no value received |
| `f_humidity` | integer | No value during tests |
| `f_power_display` | integer | No value; meaning, unit and scaling unverified |
| `f_votage` | integer | Vendor spelling; no value or confirmed scaling |
| `f_electricity` | integer | No value; accumulation period and unit unverified |
| `f_filterclean`, `f_e_*` | mostly boolean | Filter/error fields, mostly null; semantics unverified |
| `hardware_type`, `version` | integer / string | Conservatively redacted in diagnostics |

## Packed register

No standalone `t_temp` appeared on these devices. Target temperature is instead
decoded from `t_control_value`, following the reference implementation:

```python
target_celsius = (control_value >> 17) & 63
```

| Raw value | Decoded target | Verification |
| --- | --- | --- |
| 3343616 | 25 °C | Matched the app |
| 3212544 | 24 °C | Matched the app on two devices |

This register includes settings and separate change flags. Writes clear previous
change flags, preserve unrelated setting bits and flag only requested changes.
Different raw values can therefore encode identical temperatures.

The reference places power at bit 6 and mode in bits 9–11. Mode codes are
0=fan, 1=heat, 2=cool, 3=dry and 4=auto. Only cooling has been observed in the
test environment. Version 0.3.0 exposes all reference modes on packed-register
devices for explicit testing. Fan, Eco, quiet and swing fields are now exposed
experimentally but have not been verified on these devices. Fahrenheit packing
is not validated.

## Requests and consistency

Reads use `/apiv1/dsns/{dsn}/properties.json`. Writes submit
`{"datapoint": {"value": <integer>}}` to
`/apiv1/dsns/{dsn}/properties/t_control_value/datapoints.json`.

Commands are serialized per device within a client and read the current register
before modifying it. This is not a transaction: delayed cloud updates or another
controller can still cause races. Avoid overlapping app/HA commands during testing.

HA state currently uses standalone power/mode properties. The command test also
examines the packed register. Their updates can arrive at different times.
No entity state is optimistically changed to a requested value.
