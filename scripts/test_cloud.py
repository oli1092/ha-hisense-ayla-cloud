"""Interactive read-only cloud probe; no HA installation or saved credentials."""

import asyncio
import getpass
import json
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))

from aiohttp import ClientSession
from hisense_ayla_cloud.api import AylaCloudClient, AylaError
from hisense_ayla_cloud.const import HISENSE_EU_APP_ID, HISENSE_EU_APP_SECRET
from hisense_ayla_cloud.safe_diagnostics import safe_property
from hisense_ayla_cloud.models import DeviceSnapshot, climate_hvac_mode, climate_modes, target_temperature


async def probe(email, password):
    async with ClientSession() as session:
        client = AylaCloudClient(session, email, HISENSE_EU_APP_ID, HISENSE_EU_APP_SECRET)
        await client.async_login(password)
        password = None
        print("Login: OK")
        devices = await client.async_list_devices()
        print(f"Geräte entdeckt: {len(devices)} (erwartet: 3)")
        for index, device in enumerate(devices, 1):
            props = await client.async_get_properties(device["dsn"])
            print(f"Gerät {index}: {len(props)} Properties")
            print(json.dumps({name: safe_property(prop) for name, prop in props.items()}, indent=2))
            snapshot = DeviceSnapshot("redacted", "redacted", "redacted", props)
            print("Climate-Modus:", climate_hvac_mode(snapshot), "Modi:", climate_modes(snapshot))
            print("Solltemperatur:", target_temperature(snapshot))
        await client._force_refresh()
        await client.async_list_devices()
        print("Token-Refresh und anschließende Cloud-Abfrage: OK")


def main():
    logging.disable(logging.CRITICAL)
    if not sys.stdin.isatty():
        print("Bitte in einem interaktiven Terminal starten; keine Zugangsdaten als Argumente übergeben.")
        return 2
    email = input("HiSmart-Life-E-Mail: ").strip()
    password = getpass.getpass("Passwort (verdeckt): ")
    try:
        asyncio.run(probe(email, password))
    except AylaError as err:
        print(f"Cloud-Test fehlgeschlagen: {type(err).__name__}: {err}")
        return 1
    except (Exception, KeyboardInterrupt):
        print("Test abgebrochen oder unerwarteter Fehler; keine Serverantwort oder Zugangsdaten ausgegeben.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
