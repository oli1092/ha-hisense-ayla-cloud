"""Interactive single-device cloud command tests; nothing runs without selection."""

import asyncio
import getpass
import logging
import sys

# test_cloud sets the repository import path, but never runs on import.
from test_cloud import AylaCloudClient, AylaError, ClientSession
from test_cloud import HISENSE_EU_APP_ID, HISENSE_EU_APP_SECRET
from test_cloud import DeviceSnapshot, target_temperature, climate_hvac_mode
from test_cloud import safe_property

MEASUREMENTS = ("f_temp_in", "f_humidity", "f_power_display", "f_votage", "f_electricity")


def show_measurements(baseline, properties):
    print("Messwerte: Ausgangswert -> jetzt (Rohwerte; Einheiten/Skalierung noch nicht bestätigt)")
    for name in MEASUREMENTS:
        def safe_value(data):
            if name not in data:
                return "fehlt"
            return safe_property({**data[name], "name": name})["value"]
        print(f"  {name}: {safe_value(baseline)} -> {safe_value(properties)}")
    print("None bedeutet kein gelieferter Wert, nicht 0 oder aus.")


async def run(email, password):
    async with ClientSession() as session:
        client = AylaCloudClient(session, email, HISENSE_EU_APP_ID, HISENSE_EU_APP_SECRET)
        await client.async_login(password)
        password = None
        devices = await client.async_list_devices()
        for index, device in enumerate(devices, 1):
            props = await client.async_get_properties(device["dsn"])
            snapshot = DeviceSnapshot("", "", "", props)
            print(f"Gerät {index}: Soll {target_temperature(snapshot)} °C, Status {climate_hvac_mode(snapshot)}")
        selected = int(await asyncio.to_thread(input, "Gerätenummer (0 = Abbruch): "))
        if selected == 0:
            return
        if not 1 <= selected <= len(devices):
            raise ValueError("Ungültige Gerätenummer")
        dsn = devices[selected - 1]["dsn"]
        baseline = await client.async_get_properties(dsn)
        show_measurements(baseline, baseline)
        while True:
            print("1 = Einschalten, 2 = Ausschalten, 3 = Modus Kühlen (schaltet ein), 4 = Temperatur, 5 = Messwerte 3 Minuten beobachten, 0 = Ende")
            action = (await asyncio.to_thread(input, "Aktion: ")).strip()
            if action == "0":
                print("Test beendet. Der zuletzt gewählte Gerätezustand bleibt bestehen.")
                return
            if action == "5":
                print("Nur Lesen: drei Abfragen im Abstand von 60 Sekunden. Danach erscheint das Menü zum Ausschalten.")
                for minute in range(1, 4):
                    await asyncio.sleep(60)
                    try:
                        properties = await client.async_get_properties(dsn)
                    except AylaError as err:
                        print(f"Beobachtung unterbrochen: {type(err).__name__}; App prüfen. Ausschalten über Aktion 2 möglich.")
                        break
                    print(f"Nach {minute} Minute(n):")
                    show_measurements(baseline, properties)
                continue
            if action not in {"1", "2", "3", "4"}:
                print("Ungültige Auswahl")
                continue
            command, value = {"1": ("power", True), "2": ("power", False),
                              "3": ("mode", "cool"), "4": ("temperature", None)}[action]
            if command == "temperature":
                value = int(await asyncio.to_thread(input, "Neue Solltemperatur (16–30 °C): "))
                if not 16 <= value <= 30:
                    print("Ungültige Temperatur")
                    continue
            answer = await asyncio.to_thread(input, f"Gerät {selected}: {command} = {value}. Mit JA ausführen: ")
            if answer.strip() != "JA":
                print("Kein Schreibbefehl gesendet.")
                continue
            props = await client.async_get_properties(dsn)
            before = DeviceSnapshot("", "", "", props)
            print(f"Vorher: Soll {target_temperature(before)} °C, Status {climate_hvac_mode(before)}")
            try:
                await client.async_command(dsn, command, value)
            except AylaError as err:
                print(f"Befehl nicht bestätigt: {type(err).__name__}. App prüfen; keine automatische Wiederholung.")
                continue
            print("Cloud hat den Datapoint angenommen. Prüfe Rücklesewert …")
            for _ in range(3):
                await asyncio.sleep(5)
                props = await client.async_get_properties(dsn)
                snapshot = DeviceSnapshot("", "", "", props)
                control = snapshot.value("t_control_value")
                if type(control) is not int:
                    continue
                matched = ((command == "temperature" and target_temperature(snapshot) == value) or
                           (command == "power" and ((control >> 6) & 1) == int(value)) or
                           (command == "mode" and ((control >> 9) & 7) == 2 and ((control >> 6) & 1) == 1))
                if matched:
                    print(f"Cloud-Rücklesewert bestätigt: Soll {target_temperature(snapshot)} °C; Status {climate_hvac_mode(snapshot)}; packed_power={(control >> 6) & 1}")
                    break
            else:
                print("Befehl nach 15 Sekunden nicht bestätigt; App prüfen.")
            show_measurements(baseline, props)
            print("Bitte die Übernahme in der App prüfen. Zum Schluss mit Aktion 2 wieder ausschalten.")


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    if not sys.stdin.isatty():
        raise SystemExit("Bitte im interaktiven Terminal ausführen.")
    try:
        asyncio.run(run(input("HiSmart-Life-E-Mail: ").strip(), getpass.getpass("Passwort (verdeckt): ")))
    except (AylaError, ValueError) as err:
        print(f"Test fehlgeschlagen: {type(err).__name__}")
    except (Exception, KeyboardInterrupt):
        print("Test abgebrochen oder unerwarteter Fehler; keine sensiblen Details ausgegeben.")
