# Hisense Ayla Cloud

Cloud-only Home Assistant custom integration prototype for Hisense air conditioners
with AEH-W4E1/W4B1 modules and the HiSmart Life EU app.

## Current scope

This first milestone implements:

- HiSmart Life/Ayla login and refresh-token handling
- automatic cloud discovery
- cloud property polling (default 60 seconds)
- redacted diagnostics containing raw property metadata
- a read-only `climate` entity mapping power, mode, target temperature, indoor temperature and humidity

It deliberately does **not** use local callbacks, LAN keys, local IP addresses or
device-local HTTP. It also deliberately does not issue write commands yet. The
actual property names, value types and enum values must be verified from the
three target devices before writes are enabled.

## Installation

Install this repository as a HACS custom repository, restart Home Assistant, and
add **Hisense Ayla Cloud** under Settings → Devices & services. Use app code
`hisense-eu` and the same HiSmart Life credentials as the mobile app.

## Privacy and limitations

Credentials and tokens are never logged. Diagnostics redact account identifiers,
tokens and device DSNs. The integration requires outbound HTTPS access to the
Ayla EU cloud; cloud outages make entities unavailable. The cloud API is
unofficial and may change without notice.
