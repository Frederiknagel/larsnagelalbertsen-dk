"""
sync_news.py
=============

Henter nyhedsindlæg fra et Google Doc (publiceret som webside/HTML) og
konverterer dem til news.json, som website'et viser via news.js.

Sådan sætter du Google Doc'et op (gør dette én gang):
  1. Opret et Google Doc
  2. Skriv hvert nyhedsindlæg sådan:
     - Overskriften formateres med Docs' stil "Overskrift 2" (Heading 2)
       — det er selve indlæggets titel. Skriv evt. datoen først i
       overskriften, fx "2026-09-01 — Ny koncert i støbeskeen"
     - Almindelig brødtekst nedenunder (flere afsnit er fint,
       fed/kursiv/links bevares)
     - Næste "Overskrift 2" starter automatisk et nyt indlæg
  3. Filer -> Del -> Publicer til web -> vælg "Hele dokumentet"
     -> Udgiv (standardformatet, en webside, er det rigtige — IKKE csv)
  4. Kopiér den genererede URL og sæt den i .env som GOOGLE_DOC_HTML_URL

Kør scriptet:
    python scripts/sync_news.py

Det skriver/overskriver news.json i roden af projektet.
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
OUTPUT_FILE = PROJECT_ROOT / "news.json"

# Billeder fra Docs hentes ned og gemmes her som rigtige filer i
# repoet — Googles interne billed-URL'er (docs.google.com/docs-images-rt/...)
# har en "cross-origin-resource-policy: same-site"-header, som forhindrer
# browseren i at vise dem indlejret på et andet site end Google selv.
IMAGES_DIR = PROJECT_ROOT / "images" / "nyheder"
IMAGES_WEB_PREFIX = "../images/nyheder"  # relativt fra /nyheder/index.html

load_dotenv(PROJECT_ROOT / ".env")

DOC_HTML_URL = os.environ.get("GOOGLE_DOC_HTML_URL")

# Tags vi tillader at bevare inde i et indlægs brødtekst — alt andet
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

# Skrift-familier der tæller som "serif" — vælger forfatteren en af dem i
# Doc'et, markeres afsnittet med class="serif" (Tekster-siden viser det i
# en serif-webfont; på nyhedssiden falder det tilbage til systemets serif).
# Vi slipper bevidst ikke vilkårlige fonte løs — kun serif/ikke-serif.
SERIF_HINTS = ("times", "georgia", "garamond", "cambria", "palatino",
               "book antiqua", "minion", "serif")


def parse_doc_style_classes(soup) -> dict:
    """Bygger {klasse: {css-egenskab: værdi}} ud fra Google Docs' <style>-tags.

    Docs lægger AL formatering (tekstjustering, skrift, fed, kursiv) i
    CSS-klasser som `.c3{font-family:"Times New Roman";font-weight:700}` i
    stedet for på selve elementerne — derfor forsvandt den før, når vi kun
    beholdt en hvidliste af tags."""
    classes: dict[str, dict[str, str]] = {}
    for style in soup.find_all("style"):
        css = style.string or ""
        for rule in re.finditer(r"\.([A-Za-z0-9_-]+)\s*\{([^}]*)\}", css):
            props = classes.setdefault(rule.group(1), {})
            for decl in rule.group(2).split(";"):
                if ":" in decl:
                    key, _, val = decl.partition(":")
                    props[key.strip().lower()] = val.strip().lower()
    return classes


def _props_for(el, style_classes: dict) -> dict:
    """Slår alle CSS-egenskaber op for et elements Docs-klasser."""
    props: dict[str, str] = {}
    for cls in el.get("class", []):
        props.update(style_classes.get(cls, {}))
    return props


def _is_bold(props: dict) -> bool:
    weight = props.get("font-weight", "")
    return weight in ("bold", "bolder") or (weight.isdigit() and int(weight) >= 600)


def _is_italic(props: dict) -> bool:
    return props.get("font-style", "") == "italic"


def block_style_flags(el, style_classes: dict) -> tuple[bool, bool]:
    """(centreret, serif) for et blok-element. Tekstjusteringen ligger på
    selve afsnittet; skrift-familien typisk på <span>'ene indeni."""
    centered = serif = False
    for node in (el, *el.find_all("span")):
        props = _props_for(node, style_classes)
        if props.get("text-align") == "center":
            centered = True
        family = props.get("font-family", "").replace('"', "").replace("'", "")
        if any(hint in family for hint in SERIF_HINTS):
            serif = True
    return centered, serif


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
    """Henter et billede ned og gemmer det lokalt under images/nyheder/.

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
        print(f"    ↓ gemte nyt billede: images/nyheder/{filename}")

    return f"{IMAGES_WEB_PREFIX}/{filename}"


def clean_fragment(tag, style_classes: dict) -> str:
    """Fjerner alt undtagen en hvidliste af tags, bevarer tekst/links/billeder.

    Google Docs' fed/kursiv ligger i CSS-klasser på <span> (ikke <b>/<i>);
    de oversættes til <strong>/<em>, og resten af span'en pakkes ud."""
    for el in tag.find_all(True):
        if el.name == "span":
            props = _props_for(el, style_classes)
            bold, italic = _is_bold(props), _is_italic(props)
            if bold or italic:
                el.name = "strong" if bold else "em"
                el.attrs = {}
                if bold and italic:
                    inner = BeautifulSoup("", "html.parser").new_tag("em")
                    for child in list(el.contents):
                        inner.append(child.extract())
                    el.append(inner)
            else:
                el.unwrap()
            continue
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
    """Splitter dokumentets indhold i indlæg ved hver Heading 2 (<h2>)."""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body or soup
    style_classes = parse_doc_style_classes(soup)

    posts = []
    current = None
    blank_pending = False  # tom linje set — bliver et strofe-mellemrum hvis der følger mere

    for el in body.find_all(["h1", "h2", "p", "ul", "ol"], recursive=True):
        # En overskrift uden tekst er ikke en reel indlægs-grænse. Google
        # Docs lægger fx et indsat billede i sit eget afsnit, som kan arve
        # "Overskrift 2"-stilen fra linjen omkring — det bliver en tom <h2>
        # der kun rummer et <img>. Behandl den (og billedet) som brødtekst
        # i det aktuelle indlæg i stedet for at smide den væk.
        is_heading = el.name in ("h1", "h2") and el.get_text(strip=True) != ""
        centered, serif = block_style_flags(el, style_classes)
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
            blank_pending = False
            if centered:
                current["title_align"] = "center"
            if serif:
                current["title_serif"] = True
        elif current is not None:
            fragment = clean_fragment(el, style_classes)
            if not fragment:
                # tom linje: gem den kun hvis der allerede er indhold — så
                # bliver den til et strofe-mellemrum; efterfølgende tomme
                # linjer i slutningen bliver bare droppet.
                blank_pending = blank_pending or bool(current["body_parts"])
                continue
            tag = el.name if el.name in ("ul", "ol") else "p"
            names = [name for name, on in (("center", centered), ("serif", serif)) if on]
            if blank_pending:
                names.append("gap")
                blank_pending = False
            attr = f' class="{" ".join(names)}"' if names else ""
            current["body_parts"].append(f"<{tag}{attr}>{fragment}</{tag}>")

    if current and current["body_parts"]:
        posts.append(current)

    for post in posts:
        post["body_html"] = "".join(post.pop("body_parts"))

    return posts


def write_news_json(posts: list[dict]) -> None:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"\nSkrev {len(posts)} nyhed(er) til {OUTPUT_FILE}")


def main() -> int:
    if not DOC_HTML_URL:
        print(
            "Fejl: GOOGLE_DOC_HTML_URL er ikke sat.\n"
            "Kopiér .env.sample til .env og udfyld linket til dit publicerede Google Doc.",
            file=sys.stderr,
        )
        return 1

    print("Henter nyheder fra Google Doc...")
    html = fetch_doc_html(DOC_HTML_URL)

    print("Parser indlæg:")
    posts = parse_html_to_posts(html)
    for p in posts:
        print(f"  ✓ {p.get('date') or '(ingen dato)'} — {p['title']}")

    write_news_json(posts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
