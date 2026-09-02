"""
sync_texts.py
==============

Henter tekster/digte fra et Google Doc (publiceret som webside/HTML)
og konverterer dem til texts.json, som website'et viser via texts.js.

Samme mønster og opsætning som sync_news.py — se den for uddybning.
Kort version:
  1. Opret et Google Doc
  2. Skriv hver tekst/digt sådan:
     - Overskriften formateres med Docs' stil "Overskrift 2" (Heading 2)
       — det er tekstens titel. Skriv evt. datoen først i overskriften,
       fx "2026-09-01 — Titel på digt"
     - Selve teksten/digtet nedenunder (linjeskift, fed/kursiv bevares)
     - Næste "Overskrift 2" starter automatisk en ny tekst
  3. Filer -> Del -> Publicer til web -> vælg "Hele dokumentet"
     -> Udgiv (standardformatet, en webside, er det rigtige — IKKE csv)
  4. Kopiér den genererede URL og sæt den i .env som GOOGLE_TEXTS_DOC_HTML_URL

Kør scriptet:
    python scripts/sync_texts.py

Det skriver/overskriver texts.json i roden af projektet.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_FILE = PROJECT_ROOT / "texts.json"

# Billeder fra Docs hentes ned og gemmes her som rigtige filer i
# repoet — Googles interne billed-URL'er (docs.google.com/docs-images-rt/...)
# har en "cross-origin-resource-policy: same-site"-header, som forhindrer
# browseren i at vise dem indlejret på et andet site end Google selv.
IMAGES_DIR = PROJECT_ROOT / "images" / "tekster"
IMAGES_WEB_PREFIX = "../images/tekster"  # relativt fra /tekster/index.html

load_dotenv(PROJECT_ROOT / ".env")

DOC_HTML_URL = os.environ.get("GOOGLE_TEXTS_DOC_HTML_URL")

# Tags vi tillader at bevare inde i en teksts brødtekst — alt andet
# (Google Docs' egne <span class="c12">-stilarter, <font>, osv.) luges ud.
ALLOWED_TAGS = {"p", "a", "strong", "b", "em", "i", "br", "ul", "ol", "li", "img"}

# Attributter vi beholder per tilladt tag — alt andet strippes (fx Docs'
# egne inline width/height/style på billeder, som ville forhindre vores
# responsive CSS i at virke).
ALLOWED_ATTRS = {"a": {"href"}, "img": {"src", "alt"}}

# Docs-eksporten bruger typisk YYYY-MM-DD eller "1. september 2026"-agtige
# formater i starten af overskriften, hvis forfatteren skriver det sådan.
# Vi forsøger at fange et rent ISO-dato-mønster; ellers er date "" og
# hele overskriften bruges som titel uændret.
DATE_PREFIX_RE = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})\s*[—\-:]?\s*(.*)$")


def fetch_doc_html(url: str) -> str:
    """Henter det publicerede Google Doc som rå HTML."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    response.encoding = "utf-8"  # samme fælde som med Sheets-CSV'en
    return response.text


def unwrap_google_redirect(href: str) -> str:
    """Docs pakker links ind som 'https://www.google.com/url?q=<mål>&...' —
    udpak det rigtige mål-link i stedet for at beholde omvejen."""
    parsed = urlparse(href)
    if parsed.netloc == "www.google.com" and parsed.path == "/url":
        target = parse_qs(parsed.query).get("q")
        if target:
            return target[0]
    return href


def download_image(url: str) -> str | None:
    """Henter et billede ned og gemmer det lokalt under images/tekster/.

    Filnavnet er en hash af selve billedindholdet, så gentagne kørsler
    ikke skaber dubletter eller unødige git-ændringer, hvis billedet
    ikke har ændret sig. Returnerer den relative sti scriptet skal
    bruge i den udgivede HTML, eller None hvis hentningen fejlede."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as err:
        print(f"    ⚠ kunne ikke hente billede ({url}): {err}", file=sys.stderr)
        return None

    content = response.content
    digest = hashlib.md5(content).hexdigest()[:16]

    content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    ext = mimetypes.guess_extension(content_type) or ".jpg"
    if ext == ".jpe":
        ext = ".jpg"

    filename = f"{digest}{ext}"
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    filepath = IMAGES_DIR / filename
    if not filepath.exists():
        filepath.write_bytes(content)
        print(f"    ↓ gemte nyt billede: images/tekster/{filename}")

    return f"{IMAGES_WEB_PREFIX}/{filename}"


def clean_fragment(tag) -> str:
    """Fjerner alt undtagen en hvidliste af tags, bevarer tekst/links/billeder."""
    for el in tag.find_all(True):
        if el.name not in ALLOWED_TAGS:
            el.unwrap()
            continue
        allowed_attrs = ALLOWED_ATTRS.get(el.name, set())
        el.attrs = {k: v for k, v in el.attrs.items() if k in allowed_attrs}
        if el.name == "a" and el.get("href"):
            el["href"] = unwrap_google_redirect(el["href"])
    # billeder hentes ned og gemmes lokalt (se download_image) — Googles
    # egne URL'er kan ikke vises indlejret på vores site. Billeder der
    # ikke kan hentes, eller som ikke havde en gyldig src i forvejen,
    # luges væk i stedet for at give et ødelagt billed-ikon på sitet.
    for img in tag.find_all("img"):
        src = img.get("src")
        local_src = download_image(src) if src else None
        if local_src:
            img["src"] = local_src
        else:
            img.decompose()
    return tag.decode_contents().strip()


def parse_html_to_posts(html: str) -> list[dict]:
    """Splitter dokumentets indhold i tekster ved hver Heading 2 (<h2>)."""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body or soup

    posts = []
    current = None

    for el in body.find_all(["h1", "h2", "p", "ul", "ol"], recursive=True):
        # En overskrift uden tekst er ikke en reel tekst-grænse. Google
        # Docs lægger fx et indsat billede i sit eget afsnit, som kan arve
        # "Overskrift 2"-stilen fra linjen omkring — det bliver en tom <h2>
        # der kun rummer et <img>. Behandl den (og billedet) som brødtekst
        # i den aktuelle tekst i stedet for at smide den væk.
        is_heading = el.name in ("h1", "h2") and el.get_text(strip=True) != ""
        if is_heading:
            if current and current["body_parts"]:
                posts.append(current)
            heading_text = el.get_text(strip=True)
            match = DATE_PREFIX_RE.match(heading_text)
            if match:
                date_value, title = match.group(1), match.group(2).strip()
            else:
                date_value, title = "", heading_text
            current = {"date": date_value, "title": title or heading_text, "body_parts": []}
        elif current is not None:
            fragment = clean_fragment(el)
            if fragment:
                current["body_parts"].append(f"<{el.name}>{fragment}</{el.name}>" if el.name in ("ul", "ol") else fragment)

    if current and current["body_parts"]:
        posts.append(current)

    for post in posts:
        post["body_html"] = "".join(
            part if part.startswith("<ul") or part.startswith("<ol") else f"<p>{part}</p>"
            for part in post.pop("body_parts")
        )

    return posts


def write_texts_json(posts: list[dict]) -> None:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"\nSkrev {len(posts)} tekst(er) til {OUTPUT_FILE}")


def main() -> int:
    if not DOC_HTML_URL:
        print(
            "Fejl: GOOGLE_TEXTS_DOC_HTML_URL er ikke sat.\n"
            "Kopiér .env.sample til .env og udfyld linket til dit publicerede Google Doc.",
            file=sys.stderr,
        )
        return 1

    print("Henter tekster fra Google Doc...")
    html = fetch_doc_html(DOC_HTML_URL)

    print("Parser indlæg:")
    posts = parse_html_to_posts(html)
    for p in posts:
        print(f"  ✓ {p.get('date') or '(ingen dato)'} — {p['title']}")

    write_texts_json(posts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
