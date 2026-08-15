"""
sync_events.py
================

Henter koncertlisten fra et Google Sheet (publiceret som CSV) og
konverterer den til events.json, som website'et viser via script.js.

Sådan sætter du Google Sheet'et op (gør dette én gang):
  1. Opret et ark med disse kolonner i første række (præcis disse navne):
     date | time | venue | city | title | project | link
  2. date skal skrives som YYYY-MM-DD, fx 2026-09-12
     project er valgfri — skriv fx "STGYE" for Stan Gets In Your Eyes-
     koncerter, eller lad feltet stå tomt for løsere/frilance-gigs
  3. Filer -> Del -> Publicer til web -> vælg det relevante ark
     -> vælg format "Kommasepareret værdier (.csv)" -> Udgiv
  4. Kopiér den genererede URL og sæt den i .env som GOOGLE_SHEET_CSV_URL

Kør scriptet:
    python scripts/sync_events.py

Det skriver/overskriver events.json i roden af projektet.
"""

import csv
import io
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# --- opsætning af stier og miljøvariabler -----------------------------

# Denne fils placering, så scriptet virker uanset hvorfra det køres fra
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_FILE = PROJECT_ROOT / "events.json"

load_dotenv(PROJECT_ROOT / ".env")

SHEET_CSV_URL = os.environ.get("GOOGLE_SHEET_CSV_URL")

# Kolonner vi forventer fra arket, og hvordan de skal hedde i JSON-outputtet.
# (Samme navne her, men adskilt så det er nemt at ændre senere.)
EXPECTED_COLUMNS = ["date", "time", "venue", "city", "title", "project", "link"]


def fetch_sheet_csv(url: str) -> str:
    """Henter det publicerede Google Sheet som rå CSV-tekst."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # kaster en fejl hvis fx URL'en er forkert (404 osv.)

    # Googles CSV-endpoint sender ikke altid "charset=utf-8" i sin
    # Content-Type-header. Uden det gætter requests på "ISO-8859-1"
    # (HTTP-standardens fallback for text/*), selvom body rent faktisk
    # er UTF-8 — det giver mojibake på æøå (fx "Orø" bliver "OrÃ¸").
    # Vi tvinger derfor UTF-8 eksplicit i stedet for at stole på gættet.
    response.encoding = "utf-8"
    return response.text


def parse_csv_to_events(csv_text: str) -> list[dict]:
    """Parser CSV-teksten til en liste af dicts, ét dict per koncert."""
    reader = csv.DictReader(io.StringIO(csv_text))

    events = []
    for row_number, row in enumerate(reader, start=2):  # række 1 er header
        date_value = (row.get("date") or "").strip()

        if not date_value:
            # springer tomme rækker over i stedet for at fejle
            continue

        event = {column: (row.get(column) or "").strip() for column in EXPECTED_COLUMNS}
        events.append(event)
        print(f"  ✓ række {row_number}: {event['date']} — {event['venue'] or '(ingen spillested angivet)'}")

    return events


def write_events_json(events: list[dict]) -> None:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print(f"\nSkrev {len(events)} koncert(er) til {OUTPUT_FILE}")


def main() -> int:
    if not SHEET_CSV_URL:
        print(
            "Fejl: GOOGLE_SHEET_CSV_URL er ikke sat.\n"
            "Kopiér .env.sample til .env og udfyld linket til dit publicerede Google Sheet.",
            file=sys.stderr,
        )
        return 1

    print(f"Henter koncertliste fra Google Sheet...")
    csv_text = fetch_sheet_csv(SHEET_CSV_URL)

    print("Parser rækker:")
    events = parse_csv_to_events(csv_text)

    write_events_json(events)
    return 0


if __name__ == "__main__":
    sys.exit(main())
