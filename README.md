# PrairieComps (MVP)

Free asking-price comps for used farm & heavy equipment in Alberta and the Prairies.

## Quick start

```bash
cd /workspace/prairiecomps
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt  # optional
.venv/bin/python scripts/collect_listings.py   # weekly refresh
.venv/bin/python scripts/build_site.py
python3 -m http.server 8080 --directory site
```

Open http://127.0.0.1:8080/

## Layout

- `docs/SOURCES.md` — allow/deny table with robots/terms rationale
- `scripts/collect_listings.py` — polite collector (re-runnable)
- `scripts/build_site.py` — static HTML generator
- `data/listings.csv` / `listings.json` — listing dataset
- `data/market_snapshot.json` — attributed Machinery One aggregates
- `site/` — deployable static site
- `screenshots/` — homepage + model page captures

## Hosting

No authenticated deploy CLI was found on this box (`gh` logged out; no netlify/wrangler/vercel/surge). See report for go-live options (GitHub Pages or Cloudflare Pages recommended).

## Disclaimer

Prices are public **asking prices**, not appraisals or sale prices.
