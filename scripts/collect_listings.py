#!/usr/bin/env python3
"""PrairieComps listing collector — re-runnable weekly refresh.

Only hits sources documented as allowed in docs/SOURCES.md.
Respects robots constraints we checked; polite delay; no login/captcha bypass.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UA = "PrairieCompsBot/0.1 (+https://prairiecomps.local; research)"
DELAY_SEC = 1.6
TZ = ZoneInfo("America/Edmonton")

FIELDS = [
    "make",
    "model",
    "year",
    "hours",
    "price_cad",
    "location",
    "province",
    "category",
    "source",
    "source_url",
    "date_seen",
    "outlier",
]


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def fetch(url: str, timeout: int = 45) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.status, raw.decode(charset, "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if e.fp else ""
        return e.code, body
    except Exception as e:
        return 0, str(e)


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", html)
    html = re.sub(r"<[^>]+>", "\n", html)
    return unescape(html)


def parse_money(text: str) -> int | None:
    if not text:
        return None
    m = re.search(r"\$?\s*([\d]{1,3}(?:[\s,]\d{3})+|\d{4,})", text.replace("\xa0", " "))
    if not m:
        return None
    n = int(re.sub(r"[^\d]", "", m.group(1)))
    return n if n >= 1000 else None


def infer_province(location: str | None, fallback: str | None = None) -> str | None:
    if not location:
        return fallback
    loc = location.upper()
    if re.search(r"\bAB\b|ALBERTA", loc):
        return "AB"
    if re.search(r"\bSK\b|SASKATCHEWAN", loc):
        return "SK"
    if re.search(r"\bMB\b|MANITOBA", loc):
        return "MB"
    return fallback


def normalize_make(make: str | None) -> str | None:
    if not make:
        return None
    m = make.strip()
    aliases = {
        "JD": "John Deere",
        "JOHN DEERE": "John Deere",
        "CASE": "Case IH",
        "CASE IH": "Case IH",
        "CASEIH": "Case IH",
        "NEW HOLLAND": "New Holland",
        "MASSEY FERGUSON": "Massey Ferguson",
        "MASSEY": "Massey Ferguson",
        "CLAAS": "CLAAS",
        "CAT": "Caterpillar",
        "CATERPILLAR": "Caterpillar",
        "FARM KING": "Farm King",
        "FARMKING": "Farm King",
        "MK MARTIN": "MK Martin",
    }
    return aliases.get(m.upper(), m)


# ---------- Alberta AG Centre ----------

def collect_ab_ag() -> list[dict]:
    print("Collecting Alberta AG Centre…")
    status, sm = fetch("https://ab-ag.ca/listings-sitemap.xml")
    if status != 200:
        print(f"  SKIP sitemap HTTP {status}")
        return []
    urls = [
        u for u in re.findall(r"<loc>([^<]+)</loc>", sm)
        if "/listings/" in u and u.rstrip("/") != "https://ab-ag.ca/listings"
    ]
    print(f"  {len(urls)} listing URLs in sitemap")
    rows: list[dict] = []
    seen = now_iso()
    for i, url in enumerate(urls, 1):
        time.sleep(DELAY_SEC)
        code, html = fetch(url)
        if code in (401, 403):
            print(f"  BLOCKED HTTP {code} at {url} — stopping this source")
            break
        if code != 200:
            print(f"  warn HTTP {code} {url}")
            continue
        row = parse_ab_ag_listing(html, url, seen)
        if row and row.get("make"):
            rows.append(row)
            print(f"  [{i}/{len(urls)}] {row.get('year')} {row.get('make')} {row.get('model')} ${row.get('price_cad')}")
        else:
            print(f"  [{i}/{len(urls)}] parse miss {url}")
    return rows


def parse_ab_ag_listing(html: str, url: str, seen: str) -> dict | None:
    def field(label: str) -> str | None:
        # Elementor/Jet: "Make : </b>CLAAS"
        m = re.search(rf"{label}\s*:\s*</b>\s*([^<]+)", html, re.I)
        if m:
            return unescape(m.group(1)).strip() or None
        m = re.search(rf"{label}\s*:\s*</(?:b|strong)>\s*([^<]+)", html, re.I)
        if m:
            return unescape(m.group(1)).strip() or None
        m = re.search(rf"<strong>{label}</strong>\s*:\s*([^<]+)", html, re.I)
        if m:
            return unescape(m.group(1)).strip() or None
        return None

    title_m = re.search(r"<title>([^<]+)</title>", html, re.I)
    title = unescape(title_m.group(1)).split(" - ")[0].strip() if title_m else ""
    og = re.search(r'property=["\']og:title["\']\s+content=["\']([^"\']+)', html, re.I)
    if og:
        title = unescape(og.group(1)).strip() or title

    make = normalize_make(field("Make"))
    model = field("Model")
    hours_raw = field("Hours") or field("Mileage")
    loc = field("Location") or field("City")
    year = None
    ym = re.search(r"\((\d{4})\)\s*$", title)
    if ym:
        year = int(ym.group(1))
    else:
        yf = field("Year")
        if yf and re.match(r"^\d{4}$", yf.strip()):
            year = int(yf.strip())

    if not model and title:
        # "CLAAS LEXION 8700 (2022)" or "HORSCH JOKER RX30 (2023)"
        t = re.sub(r"\(\d{4}\)\s*$", "", title).strip()
        if make and t.upper().startswith(make.upper()):
            model = t[len(make) :].strip()
        else:
            parts = t.split()
            if not make and parts:
                make = normalize_make(parts[0])
                model = " ".join(parts[1:]) or None

    hours = None
    if hours_raw:
        hm = re.search(r"([\d,]+)", hours_raw.replace(" ", ""))
        if hm:
            hours = int(hm.group(1).replace(",", ""))

    # Prefer explicit Price: field, then first substantial $ amount
    price = None
    pm = re.search(r"Price\s*:\s*</b>\s*:?\s*\$?([\d,\.]+)", html, re.I)
    if not pm:
        pm = re.search(r"Price\s*:\s*:?\s*\$?([\d,\.]+)", html, re.I)
    if pm:
        try:
            price = int(float(pm.group(1).replace(",", "")))
            if price < 1000:
                price = None
        except ValueError:
            price = None
    if price is None:
        prices = [parse_money(p) for p in re.findall(r"\$[\d,\s]{4,}", html)]
        prices = [p for p in prices if p and p >= 1000]
        price = prices[0] if prices else None

    category = None
    for lab in ("Category", "Body", "Type"):
        category = field(lab) or category

    if not make and not model:
        return None

    location = f"{loc}, AB" if loc and "AB" not in loc.upper() and "Alberta" not in loc else loc
    if location and "Alberta" in location and ", AB" not in location:
        location = location.replace("Alberta", "AB")

    return {
        "make": make,
        "model": model,
        "year": year,
        "hours": hours,
        "price_cad": price,
        "location": location or "Alberta",
        "province": "AB",
        "category": category,
        "source": "Alberta AG Centre",
        "source_url": url,
        "date_seen": seen,
        "outlier": False,
    }


# ---------- Western Tractor ----------

def collect_western() -> list[dict]:
    print("Collecting Western Tractor…")
    url = "https://www.westerntractor.ca/usedequipment"
    code, html = fetch(url)
    if code in (401, 403):
        print(f"  BLOCKED HTTP {code}")
        return []
    if code != 200:
        print(f"  SKIP HTTP {code}")
        return []
    seen = now_iso()
    chunks = re.split(r'class="[^"]*w-dyn-item[^"]*"', html)[1:]
    rows: list[dict] = []
    for ch in chunks:
        text = strip_tags(ch)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        # trim trailing chrome
        if "Cookie Settings" in lines:
            lines = lines[: lines.index("Cookie Settings")]
        price = None
        hours = None
        year = None
        make = None
        model = None
        city = None
        category = None
        for i, ln in enumerate(lines):
            if ln == "Engine Hours:" and i + 1 < len(lines):
                try:
                    hours = int(lines[i + 1].replace(",", ""))
                except ValueError:
                    pass
            if ln == "$" and i + 1 < len(lines) and lines[i + 1].replace(",", "").isdigit():
                price = int(lines[i + 1].replace(",", ""))
            if ln in (
                "John Deere",
                "Case IH",
                "Case",
                "New Holland",
                "Caterpillar",
                "Kubota",
                "MacDon",
                "CLAAS",
                "Massey Ferguson",
            ):
                make = ln
                if i + 1 < len(lines) and not lines[i + 1] in ("Engine Hours:", "$"):
                    # model often next
                    if not re.match(r"^(TABER|LETHBRIDGE|MEDICINE HAT|County)", lines[i + 1], re.I):
                        if not re.match(r"^\d{4}$", lines[i + 1]):
                            model = lines[i + 1]
            if re.match(r"^(19|20)\d{2}$", ln) and year is None:
                year = int(ln)
            if ln == "AB" and i >= 2:
                city = lines[i - 2] if lines[i - 1] == "," else lines[i - 1]
            if ln in (
                "Combine",
                "Track Tractor",
                "Tractor",
                "Self-Propelled Sprayer",
                "Sprayer",
                "Seeding",
                "Tillage",
            ):
                category = ln
        # Fallback model from early lines
        if make and not model:
            for ln in lines[:8]:
                if ln not in (make, "Combine", "Track Tractor", "Self-Propelled Sprayer", city or "") and not re.match(
                    r"^\d{4}$", ln
                ):
                    if re.search(r"[A-Za-z0-9]", ln) and len(ln) < 40:
                        model = ln
                        break
        if not make or not price:
            continue
        loc = f"{city}, AB" if city else "Alberta"
        rows.append(
            {
                "make": normalize_make(make),
                "model": model,
                "year": year,
                "hours": hours,
                "price_cad": price,
                "location": loc,
                "province": "AB",
                "category": category,
                "source": "Western Tractor",
                "source_url": url,
                "date_seen": seen,
                "outlier": False,
            }
        )
    print(f"  parsed {len(rows)} listings")
    return rows



# ---------- Full Line Ag (SK) ----------

def collect_full_line_ag() -> list[dict]:
    print("Collecting Full Line Ag…")
    rows: list[dict] = []
    seen = now_iso()
    for page in range(1, 12):
        url = (
            "https://fulllineag.com/equipment/used-equipment/"
            if page == 1
            else f"https://fulllineag.com/equipment/used-equipment/page/{page}/"
        )
        if page > 1:
            time.sleep(DELAY_SEC)
        code, html = fetch(url)
        if code in (401, 403):
            print(f"  BLOCKED HTTP {code}")
            break
        if code != 200:
            print(f"  page {page} HTTP {code} — stop")
            break
        chunks = re.split(r'class=["\']oxy-post-middle["\']', html)[1:]
        if not chunks:
            print(f"  page {page}: no cards")
            break
        page_rows = 0
        for ch in chunks:
            title_m = re.search(r"oxy-post-title[^>]*href=['\"]([^'\"]+)['\"]>([^<]+)", ch)
            if not title_m:
                continue
            detail_url = title_m.group(1)
            title = unescape(title_m.group(2)).strip()

            def wsnt(cls: str) -> str | None:
                m = re.search(rf'wsnt-{cls}.*?wsnt-value">(.*?)</span>', ch, re.S | re.I)
                if not m:
                    return None
                return unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() or None

            price_raw = wsnt("price")
            hours_raw = wsnt("hours")
            loc = wsnt("location")
            price = None
            if price_raw and price_raw.upper() not in ("N/A", "CALL", "CALL FOR PRICE"):
                price = parse_money(price_raw)
            hours = None
            if hours_raw:
                hm = re.search(r"([\d,]+)", hours_raw.replace(" ", ""))
                if hm:
                    hours = int(hm.group(1).replace(",", ""))
            year = None
            ym = re.match(r"^(19|20)\d{2}\b", title)
            if ym:
                year = int(ym.group(0))
            rest = re.sub(r"^(19|20)\d{2}\s+", "", title).strip()
            parts = rest.split()
            make = normalize_make(parts[0]) if parts else None
            model = " ".join(parts[1:]) if len(parts) > 1 else None
            # Multi-word makes
            if parts:
                two = " ".join(parts[:2]).upper()
                if two in ("JOHN DEERE", "NEW HOLLAND", "CASE IH", "MASSEY FERGUSON", "FULL LINE"):
                    make = normalize_make(two if two != "FULL LINE" else parts[0])
                    if two == "FULL LINE":
                        model = " ".join(parts[1:]) or None
                    else:
                        model = " ".join(parts[2:]) or None
            province = infer_province(loc, "SK")
            if not make:
                continue
            rows.append(
                {
                    "make": make,
                    "model": model,
                    "year": year,
                    "hours": hours,
                    "price_cad": price,
                    "location": loc or "Saskatchewan",
                    "province": province or "SK",
                    "category": None,
                    "source": "Full Line Ag",
                    "source_url": detail_url,
                    "date_seen": seen,
                    "outlier": False,
                }
            )
            page_rows += 1
        print(f"  page {page}: {page_rows} listings")
        if page_rows < 5 and page > 1:
            break
    print(f"  parsed {len(rows)} listings")
    return rows


# ---------- Prairie Sales (MB) ----------

def collect_prairie_sales() -> list[dict]:
    print("Collecting Prairie Sales…")
    code, sm = fetch("https://prairiesales.ca/wp-sitemap-posts-listing-1.xml")
    if code != 200:
        print(f"  SKIP sitemap HTTP {code}")
        return []
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", sm) if "/listing/" in u]
    print(f"  {len(urls)} listing URLs in sitemap")
    rows: list[dict] = []
    seen = now_iso()
    for i, url in enumerate(urls, 1):
        time.sleep(DELAY_SEC)
        code, html = fetch(url)
        if code in (401, 403):
            print(f"  BLOCKED HTTP {code} — stopping this source")
            break
        if code != 200:
            print(f"  warn HTTP {code} {url}")
            continue
        row = parse_prairie_sales_listing(html, url, seen)
        if row and row.get("make"):
            rows.append(row)
            print(f"  [{i}/{len(urls)}] {row.get('year')} {row.get('make')} {row.get('model')} ${row.get('price_cad')}")
        else:
            print(f"  [{i}/{len(urls)}] parse miss {url}")
    return rows


def parse_prairie_sales_listing(html: str, url: str, seen: str) -> dict | None:
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "\n", text)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]

    def after(label: str) -> str | None:
        for i, ln in enumerate(lines):
            if ln == label and i + 1 < len(lines):
                return lines[i + 1]
        return None

    year = None
    yraw = after("Year")
    if yraw and re.match(r"^\d{4}$", yraw):
        year = int(yraw)
    make = normalize_make(after("Make"))
    model = after("Model")
    hours = None
    hraw = after("Hours")
    if hraw:
        hm = re.search(r"([\d,]+)", hraw.replace(" ", ""))
        if hm:
            hours = int(hm.group(1).replace(",", ""))
    loc = after("Location")
    # Our Price appears as 'Our Price' then '$' then amount
    price = None
    for i, ln in enumerate(lines):
        if ln == "Our Price":
            # next non-empty money-ish
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j] in ("$", "CAD"):
                    continue
                price = parse_money(lines[j] if lines[j].startswith("$") else f"${lines[j]}")
                if price:
                    break
            break
    if price is None:
        # fallback first substantial $ after Our Price marker in raw html entities
        m = re.search(r"Our Price.*?\$[\s\u00a0]*([\d,]+)", unescape(html), re.S | re.I)
        if m:
            try:
                price = int(m.group(1).replace(",", ""))
            except ValueError:
                price = None

    if not make:
        # title fallback: "2014 CASE 7230"
        title_m = re.search(r"<title>([^<]+)</title>", html, re.I)
        if title_m:
            title = unescape(title_m.group(1)).split("–")[0].split("-")[0].strip()
            tm = re.match(r"^(?:(19|20)\d{2}\s+)?(.+)$", title)
            if tm:
                if title[:4].isdigit():
                    year = year or int(title[:4])
                    rest = title[5:].strip()
                else:
                    rest = title
                parts = rest.split()
                if parts:
                    make = normalize_make(parts[0])
                    model = model or " ".join(parts[1:]) or None

    if not make:
        return None
    province = infer_province(loc, "MB")
    return {
        "make": make,
        "model": model,
        "year": year,
        "hours": hours,
        "price_cad": price,
        "location": loc or "Manitoba",
        "province": province or "MB",
        "category": after("Category") or after("Condition"),
        "source": "Prairie Sales",
        "source_url": url,
        "date_seen": seen,
        "outlier": False,
    }


# ---------- Flaman Agriculture (AB/SK) ----------

def collect_flaman() -> list[dict]:
    print("Collecting Flaman Agriculture…")
    url = "https://www.flamanagriculture.com/inventory?type=used"
    code, html = fetch(url)
    if code in (401, 403):
        print(f"  BLOCKED HTTP {code}")
        return []
    if code != 200:
        print(f"  SKIP HTTP {code}")
        return []
    seen = now_iso()
    rows: list[dict] = []
    parts = html.split("<!-- .item -->")
    for part in parts:
        link_m = re.search(r'<a class="over" href="([^"]+)"[^>]*title="([^"]*)"', part)
        if not link_m:
            # fallback: over link + h3
            link_m = re.search(r'<a class="over" href="([^"]+)"', part)
            title_m = re.search(r"<h3>([^<]+)</h3>", part)
            if not link_m or not title_m:
                continue
            detail = link_m.group(1)
            title = unescape(title_m.group(1)).strip()
        else:
            detail = link_m.group(1)
            title = unescape(link_m.group(2) or "").strip()
            if not title:
                tm = re.search(r"<h3>([^<]+)</h3>", part)
                title = unescape(tm.group(1)).strip() if tm else ""
        if not title:
            continue
        price_m = re.search(r"\$([\d,]+)", part)
        price = int(price_m.group(1).replace(",", "")) if price_m else None
        if price is not None and price < 1000:
            price = None
        loc_m = re.search(r'<div class="location"[^>]*>.*?<strong>([^<]+)</strong>', part, re.S)
        loc = loc_m.group(1).strip() if loc_m else None
        year = None
        ym = re.match(r"^(19|20)\d{2}\b", title)
        if ym:
            year = int(ym.group(0))
        rest = re.sub(r"^(19|20)\d{2}\s+", "", title).strip()
        parts_t = rest.split()
        make = normalize_make(parts_t[0]) if parts_t else None
        model = " ".join(parts_t[1:]) if len(parts_t) > 1 else None
        if parts_t:
            two = " ".join(parts_t[:2]).upper()
            if two in ("JOHN DEERE", "NEW HOLLAND", "CASE IH", "MASSEY FERGUSON", "FARM KING", "MK MARTIN"):
                make = normalize_make(two)
                model = " ".join(parts_t[2:]) or None
        province = infer_province(loc, "AB")
        if not make:
            continue
        rows.append(
            {
                "make": make,
                "model": model,
                "year": year,
                "hours": None,
                "price_cad": price,
                "location": loc or "Alberta",
                "province": province or "AB",
                "category": "Used farm equipment",
                "source": "Flaman Agriculture",
                "source_url": detail if detail.startswith("http") else f"https://www.flamanagriculture.com{detail}",
                "date_seen": seen,
                "outlier": False,
            }
        )
    print(f"  parsed {len(rows)} listings")
    return rows



# ---------- Machinery One market aggregates (attribution only) ----------

def collect_machinery_one_market() -> dict:
    print("Fetching Machinery One published market aggregates (attribution only)…")
    url = "https://www.machineryone.ca/market"
    code, html = fetch(url)
    if code != 200:
        print(f"  SKIP HTTP {code}")
        return {}
    # Province table rows from markdown-ish HTML tables
    provinces = []
    # Parse table rows: Province | Listings | Median | Range
    for m in re.finditer(
        r"<tr[^>]*>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([\d,]+)</td>\s*<td[^>]*>\$?([\d,]+)</td>\s*<td[^>]*>\$?([\d,]+)\s*-\s*\$?([\d,]+)</td>",
        html,
        re.I,
    ):
        name = unescape(m.group(1)).strip()
        if name in ("Type", "Province", "Brand"):
            continue
        provinces.append(
            {
                "name": name,
                "listings": int(m.group(2).replace(",", "")),
                "median_cad": int(m.group(3).replace(",", "")),
                "low_cad": int(m.group(4).replace(",", "")),
                "high_cad": int(m.group(5).replace(",", "")),
            }
        )
    # Fallback: strip to text tables if HTML pattern misses
    if not provinces:
        text = strip_tags(html)
        # Alberta line from known format
        for prov in ("Alberta", "Saskatchewan", "Manitoba"):
            m = re.search(
                rf"{prov}\s+([\d,]+)\s+\$?([\d,]+)\s+\$?([\d,]+)\s*-\s*\$?([\d,]+)",
                text,
            )
            if m:
                provinces.append(
                    {
                        "name": prov,
                        "listings": int(m.group(1).replace(",", "")),
                        "median_cad": int(m.group(2).replace(",", "")),
                        "low_cad": int(m.group(3).replace(",", "")),
                        "high_cad": int(m.group(4).replace(",", "")),
                    }
                )
    snap = {
        "source": "Machinery One",
        "source_url": url,
        "date_seen": now_iso(),
        "attribution": (
            "Province and brand asking-price medians published on Machinery One’s "
            "public market page. Figures are dealer asking prices, not sale prices. "
            "PrairieComps does not scrape Machinery One listing inventory (prohibited by their terms)."
        ),
        "provinces": [p for p in provinces if p["name"] in ("Alberta", "Saskatchewan", "Manitoba", "British Columbia")],
        "all_provinces_found": provinces,
    }
    print(f"  provinces parsed: {len(snap['provinces'])} prairie-relevant of {len(provinces)} total rows")
    return snap


def dedupe(rows: list[dict]) -> list[dict]:
    out = []
    seen = set()
    for r in rows:
        key = (
            r.get("source"),
            r.get("source_url"),
            r.get("make"),
            r.get("model"),
            r.get("year"),
            r.get("hours"),
            r.get("price_cad"),
            r.get("location"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def write_outputs(rows: list[dict], market: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    rows = dedupe(rows)
    json_path = DATA / "listings.json"
    csv_path = DATA / "listings.csv"
    meta_path = DATA / "collection_meta.json"
    market_path = DATA / "market_snapshot.json"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    if market:
        with market_path.open("w", encoding="utf-8") as f:
            json.dump(market, f, indent=2, ensure_ascii=False)

    priced = sum(1 for r in rows if r.get("price_cad"))
    makes = sorted({r["make"] for r in rows if r.get("make")})
    models = sorted({f"{r.get('make')} {r.get('model')}".strip() for r in rows if r.get("make") and r.get("model")})
    meta = {
        "collected_at": now_iso(),
        "timezone": "America/Edmonton",
        "listing_count": len(rows),
        "priced_count": priced,
        "make_count": len(makes),
        "model_count": len(models),
        "sources": sorted({r["source"] for r in rows}),
        "paths": {"json": str(json_path), "csv": str(csv_path), "market": str(market_path)},
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


def flag_outliers(rows: list[dict]) -> list[dict]:
    """Mark obviously bad asking prices (kept in dataset, excluded from medians later)."""
    floors = {
        "combine": 25000,
        "tractor": 15000,
        "sprayer": 15000,
        "windrower": 20000,
    }
    for r in rows:
        price = r.get("price_cad")
        if not price:
            r["outlier"] = False
            continue
        cat = (r.get("category") or "").lower()
        blob = f"{r.get('make','')} {r.get('model','')} {cat}".lower()
        bad = False
        if price < 1000:
            bad = True
        for key, floor in floors.items():
            if key in cat and price < floor:
                bad = True
        # Heuristic: combine models priced like a pallet fork
        if price < 10000 and any(k in blob for k in ("lexion", " cr8", " cr9", "s790", "s780", "x9-1000", "combine")):
            if "header" not in blob and "pall" not in blob and "platform" not in blob:
                bad = True
        r["outlier"] = bad
    return rows


def main() -> int:
    rows: list[dict] = []
    rows.extend(collect_ab_ag())
    rows.extend(collect_western())
    rows.extend(collect_full_line_ag())
    rows.extend(collect_prairie_sales())
    rows.extend(collect_flaman())
    rows = flag_outliers(rows)
    market = collect_machinery_one_market()
    write_outputs(rows, market)
    return 0


if __name__ == "__main__":
    sys.exit(main())
