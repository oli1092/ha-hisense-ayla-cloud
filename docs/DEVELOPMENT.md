# Development and roadmap

## Structure

Integration modules are under `custom_components/hisense_ayla_cloud`:

| File | Responsibility |
| --- | --- |
| `api.py` | Async login, refresh, discovery, reads and cloud writes |
| `commands.py` | Validation and packed-command construction |
| `models.py` | Snapshots and climate mapping |
| `config_flow.py` | Setup, reauthentication and options |
| `coordinator.py` | Polling, backoff and availability |
| `climate.py` | Climate entity and HA services |
| `diagnostics.py`, `safe_diagnostics.py` | Filtered diagnostics |

Standalone tools are in `scripts/`; regression tests are in `tests/`.

## Automated checks

From the repository root:

```shell
uv run --no-project --python 3.12 --with pytest --with pytest-asyncio --with aiohttp python -m pytest -q
git diff --check
```

Version 0.2.0 has 29 passing tests covering token parsing, mocked login/discovery,
refresh after rejection, token-rotation callbacks, property normalization,
redaction, numeric modes, verified temperature samples and cloud writes.

These unit tests are not a complete Home Assistant harness. Config-flow UI,
coordinator scheduling, reauth lifecycle, service dispatch and restart behavior
still need integration tests. A full HA compatibility matrix and HACS/hassfest
validation have not been completed.

## Contributions

- Keep networking asynchronous and cloud-only; do not add LAN keys, callbacks or device-IP access.
- Verify real properties, types, units and writable metadata before adding controls.
- Distinguish reference mappings from evidence collected on actual hardware.
- Preserve unrelated fields and never optimistically claim command execution.
- Add meaningful regression tests and update the feature matrix.
- Never commit credentials, tokens, device identifiers or personal raw diagnostics.
  Use synthetic or anonymized fixtures.

## Roadmap

Version 0.3.0 adds reference-based experimental controls and raw sensor/binary
sensor entities. There are 51 passing unit tests, including missing measurements,
packed flag preservation and refusal of read-only writes. Hardware validation of
the new controls remains pending; earlier 0.2.0 test observations still apply.

1. Complete HA services, options, restart and reauth validation (basic entity creation confirmed).
2. Verify real transitions between modes and firmware capability metadata.
3. Validate device-offline detection, freshness and concurrent app/HA changes.
4. Verify exposed experimental fan speed, swing and angle encodings.
5. Validate Eco, Quiet, Turbo/Super, Backlight and 8-degree-heating switches where present.
6. Validate Sleep/swing-angle selects and assign measurement/error semantics only after units and polarity are established.
7. Validate additional modules and regions before claiming compatibility.
8. Establish a supported HA version range, automated HA validation, English terminal prompts and release packaging.

The current release does not yet fulfill this entire roadmap.
