#!/usr/bin/env python3
"""Generate PrairieComps static site from data/listings.json."""
from __future__ import annotations

import json
import math
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SITE = ROOT / "site"
TZ = ZoneInfo("America/Edmonton")

CONTACT_EMAIL = "dealers@prairiecomps.example"  # placeholder
GENERAL_EMAIL = "hello@prairiecomps.example"  # placeholder


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "model"


def money(n) -> str:
    if n is None:
        return "—"
    return f"${int(n):,}"


def load_listings() -> list[dict]:
    return json.loads((DATA / "listings.json").read_text(encoding="utf-8"))


def load_market() -> dict:
    p = DATA / "market_snapshot.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def group_models(listings: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in listings:
        make = (r.get("make") or "").strip()
        model = (r.get("model") or "").strip()
        if not make or not model:
            continue
        key = f"{make} {model}"
        groups[key].append(r)
    return groups


def model_stats(rows: list[dict]) -> dict:
    prices = sorted(r["price_cad"] for r in rows if r.get("price_cad"))
    hours = [r["hours"] for r in rows if r.get("hours") is not None]
    years = [r["year"] for r in rows if r.get("year")]
    provinces = sorted({r.get("province") for r in rows if r.get("province")})
    return {
        "count": len(rows),
        "priced_count": len(prices),
        "median": int(median(prices)) if prices else None,
        "low": prices[0] if prices else None,
        "high": prices[-1] if prices else None,
        "hours_min": min(hours) if hours else None,
        "hours_max": max(hours) if hours else None,
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "provinces": provinces,
        "make": rows[0].get("make"),
        "model": rows[0].get("model"),
    }


def layout(title: str, body: str, active: str = "", description: str = "") -> str:
    desc = description or "Fair-market used farm and heavy equipment asking prices for Alberta and the Prairies."
    nav = [
        ("index.html", "home", "Home"),
        ("for-dealers.html", "dealers", "For Dealers"),
        ("about.html", "about", "About"),
    ]
    links = []
    for href, key, label in nav:
        cls = ' class="active"' if key == active else ""
        links.append(f'<a href="{href}"{cls}>{label}</a>')
    nav_html = "\n        ".join(links)
    return f"""<!DOCTYPE html>
<html lang="en-CA">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <meta name="theme-color" content="#1b4332" />
  <link rel="stylesheet" href="css/styles.css" />
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="wrap header-inner">
      <a class="logo" href="index.html">Prairie<span>Comps</span></a>
      <nav class="nav" aria-label="Primary">
        {nav_html}
      </nav>
    </div>
  </header>
  <main id="main">
{body}
  </main>
  <footer class="site-footer">
    <div class="wrap footer-grid">
      <div>
        <strong>PrairieComps</strong>
        <p>Asking-price comps for used farm &amp; heavy equipment across Alberta and the Prairies. Free for buyers; featured placement for dealers.</p>
      </div>
      <div>
        <strong>Disclaimer</strong>
        <p>Prices shown are <em>asking prices</em> from public dealer listings, not appraisals, auction hammer prices, or guaranteed sale values. Always verify with the seller and inspect equipment before buying.</p>
      </div>
      <div>
        <strong>Contact</strong>
        <p>General: <a href="mailto:{GENERAL_EMAIL}">{GENERAL_EMAIL}</a><br />
        Dealers: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
        <p class="muted">Based in Red Deer, Alberta. Street address intentionally omitted.</p>
      </div>
    </div>
    <div class="wrap footer-bottom">
      <span>© {datetime.now(TZ).year} PrairieComps · MVP</span>
      <span>Not affiliated with any OEM or auction house.</span>
    </div>
  </footer>
  <script src="js/app.js"></script>
</body>
</html>
"""


def build_css() -> str:
    return """:root {
  --bg: #f4f1ea;
  --card: #ffffff;
  --ink: #14231b;
  --muted: #5b6b62;
  --brand: #1b4332;
  --brand-2: #2d6a4f;
  --accent: #bc6c25;
  --line: #d9e0da;
  --ok: #40916c;
  --shadow: 0 10px 30px rgba(20, 35, 27, 0.08);
  --radius: 16px;
  --max: 1100px;
  --font: "Segoe UI", system-ui, -apple-system, sans-serif;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: var(--font);
  color: var(--ink);
  background:
    radial-gradient(1200px 500px at 10% -10%, #d8e2d4 0%, transparent 60%),
    radial-gradient(900px 400px at 100% 0%, #efe2cf 0%, transparent 55%),
    var(--bg);
  line-height: 1.5;
}
a { color: var(--brand-2); }
.skip {
  position: absolute; left: -999px; top: 0; background: #000; color: #fff; padding: .5rem 1rem;
}
.skip:focus { left: 0; z-index: 99; }
.wrap { width: min(100% - 2rem, var(--max)); margin-inline: auto; }
.site-header {
  position: sticky; top: 0; z-index: 20;
  backdrop-filter: blur(10px);
  background: rgba(244, 241, 234, 0.9);
  border-bottom: 1px solid var(--line);
}
.header-inner { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: .9rem 0; }
.logo {
  font-weight: 800; font-size: 1.25rem; text-decoration: none; color: var(--brand); letter-spacing: -0.02em;
}
.logo span { color: var(--accent); }
.nav { display: flex; gap: .25rem; flex-wrap: wrap; }
.nav a {
  text-decoration: none; color: var(--ink); padding: .45rem .75rem; border-radius: 999px; font-weight: 600; font-size: .95rem;
}
.nav a:hover, .nav a.active { background: var(--brand); color: #fff; }
.hero {
  padding: 2.5rem 0 1.5rem;
}
.hero-card, .card, .stat, .listing, .tier {
  background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow);
}
.hero-card { padding: 1.75rem; }
.hero h1 { margin: 0 0 .5rem; font-size: clamp(1.8rem, 4vw, 2.6rem); line-height: 1.15; letter-spacing: -0.03em; }
.lead { color: var(--muted); font-size: 1.05rem; max-width: 52ch; }
.badge {
  display: inline-block; background: #e9f5ee; color: var(--brand); font-weight: 700; font-size: .78rem;
  padding: .25rem .6rem; border-radius: 999px; margin-bottom: .75rem; text-transform: uppercase; letter-spacing: .04em;
}
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; margin: 1.25rem 0 0; }
.stat { padding: 1rem; }
.stat .n { font-size: 1.45rem; font-weight: 800; color: var(--brand); }
.stat .l { color: var(--muted); font-size: .85rem; }
.filters {
  display: grid; grid-template-columns: 1.2fr 1fr 1fr auto; gap: .6rem; margin-top: 1.25rem;
}
.filters input, .filters select, .btn, .mailto {
  font: inherit; border-radius: 12px; border: 1px solid var(--line); padding: .7rem .85rem; background: #fff;
}
.btn, .mailto {
  background: var(--brand); color: #fff; border-color: var(--brand); font-weight: 700; text-decoration: none;
  display: inline-flex; align-items: center; justify-content: center; cursor: pointer;
}
.btn.secondary { background: #fff; color: var(--brand); }
.btn:hover, .mailto:hover { background: var(--brand-2); border-color: var(--brand-2); color: #fff; }
.section { padding: 1.5rem 0 2.5rem; }
.section h2 { margin: 0 0 1rem; font-size: 1.4rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: .9rem; }
.model-card { padding: 1rem 1.1rem; text-decoration: none; color: inherit; transition: transform .15s ease, box-shadow .15s ease; }
.model-card:hover { transform: translateY(-2px); box-shadow: 0 14px 34px rgba(20,35,27,.12); }
.model-card h3 { margin: 0 0 .35rem; font-size: 1.05rem; }
.model-card .meta { color: var(--muted); font-size: .9rem; }
.price-row { display: flex; justify-content: space-between; gap: .5rem; margin-top: .7rem; font-weight: 700; }
.price-row span { color: var(--muted); font-weight: 600; font-size: .85rem; }
.table-wrap { overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--line); background: #fff; }
table { width: 100%; border-collapse: collapse; font-size: .95rem; }
th, td { padding: .7rem .8rem; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
th { background: #eef4ef; font-size: .8rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
.muted { color: var(--muted); }
.callout {
  background: #fff7ed; border: 1px solid #f0d3ad; border-radius: var(--radius); padding: 1rem 1.1rem; margin: 1rem 0;
}
.tiers { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }
.tier { padding: 1.25rem; }
.tier h3 { margin-top: 0; }
.tier .price { font-size: 1.8rem; font-weight: 800; color: var(--brand); }
.tier ul { padding-left: 1.1rem; color: var(--muted); }
.site-footer { border-top: 1px solid var(--line); background: #e9efe8; margin-top: 2rem; padding: 2rem 0 1.25rem; }
.footer-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem; }
.footer-grid p { color: var(--muted); font-size: .92rem; }
.footer-bottom { display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; margin-top: 1.25rem; color: var(--muted); font-size: .85rem; }
.breadcrumbs { font-size: .9rem; color: var(--muted); margin-bottom: .75rem; }
.breadcrumbs a { color: inherit; }
.page-head { padding: 1.75rem 0 0.5rem; }
.page-head h1 { margin: 0 0 .4rem; font-size: clamp(1.6rem, 3vw, 2.2rem); }
.prose { max-width: 70ch; }
.prose h2 { margin-top: 1.6rem; }
.hidden { display: none !important; }
@media (max-width: 800px) {
  .stats { grid-template-columns: repeat(2, 1fr); }
  .filters { grid-template-columns: 1fr 1fr; }
  .footer-grid { grid-template-columns: 1fr; }
}
@media (max-width: 520px) {
  .filters { grid-template-columns: 1fr; }
  .header-inner { flex-direction: column; align-items: flex-start; }
}
"""


def build_js() -> str:
    return """(function () {
  const q = document.getElementById('q');
  const make = document.getElementById('make');
  const province = document.getElementById('province');
  const cards = Array.from(document.querySelectorAll('[data-model-card]'));
  const empty = document.getElementById('empty-state');
  if (!cards.length) return;

  function apply() {
    const term = (q && q.value || '').trim().toLowerCase();
    const mk = (make && make.value || '').toLowerCase();
    const pv = (province && province.value || '').toLowerCase();
    let shown = 0;
    cards.forEach(card => {
      const hay = (card.getAttribute('data-search') || '').toLowerCase();
      const okTerm = !term || hay.includes(term);
      const okMake = !mk || (card.getAttribute('data-make') || '').toLowerCase() === mk;
      const okProv = !pv || (card.getAttribute('data-provinces') || '').toLowerCase().includes(pv);
      const ok = okTerm && okMake && okProv;
      card.classList.toggle('hidden', !ok);
      if (ok) shown += 1;
    });
    if (empty) empty.classList.toggle('hidden', shown > 0);
  }
  [q, make, province].forEach(el => {
    if (!el) return;
    el.addEventListener('input', apply);
    el.addEventListener('change', apply);
  });
})();
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    listings = load_listings()
    market = load_market()
    groups = group_models(listings)
    ranked = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0].lower()))
    # Top models for dedicated pages (all if ≤100)
    top = ranked[:100]

    if SITE.exists():
        # clean generated pages but keep structure
        for child in list(SITE.iterdir()):
            if child.name in ("css", "js", "models"):
                continue
            if child.is_file():
                child.unlink()
        models_dir = SITE / "models"
        if models_dir.exists():
            shutil.rmtree(models_dir)
    (SITE / "css").mkdir(parents=True, exist_ok=True)
    (SITE / "js").mkdir(parents=True, exist_ok=True)
    (SITE / "models").mkdir(parents=True, exist_ok=True)

    write(SITE / "css" / "styles.css", build_css())
    write(SITE / "js" / "app.js", build_js())
    # Embed listings for client search enrichment
    write(SITE / "js" / "listings.json", json.dumps(listings, ensure_ascii=False))

    priced = [r for r in listings if r.get("price_cad")]
    overall_med = int(median([r["price_cad"] for r in priced])) if priced else None
    makes = sorted({r["make"] for r in listings if r.get("make")})
    provinces = sorted({r.get("province") for r in listings if r.get("province")})
    collected = max((r.get("date_seen") or "") for r in listings) if listings else ""

    # Homepage
    make_opts = "\n".join(f'<option value="{m}">{m}</option>' for m in makes)
    prov_opts = "\n".join(f'<option value="{p}">{p}</option>' for p in provinces)
    cards = []
    for name, rows in top:
        st = model_stats(rows)
        slug = slugify(name)
        href = f"models/{slug}.html"
        provs = ",".join(st["provinces"])
        cards.append(
            f"""<a class="card model-card" data-model-card href="{href}" data-make="{st['make']}" data-provinces="{provs}" data-search="{name} {provs}">
  <h3>{name}</h3>
  <div class="meta">{st['count']} listing{'s' if st['count']!=1 else ''} · {provs or 'Prairies'}</div>
  <div class="price-row"><div>{money(st['median'])}<div class="meta">median ask</div></div>
  <div><span>Low {money(st['low'])}</span><br /><span>High {money(st['high'])}</span></div></div>
</a>"""
        )

    market_bits = []
    for p in market.get("provinces") or []:
        market_bits.append(
            f"<tr><td>{p['name']}</td><td>{p['listings']:,}</td><td>{money(p['median_cad'])}</td><td>{money(p['low_cad'])} – {money(p['high_cad'])}</td></tr>"
        )
    market_html = ""
    if market_bits:
        market_html = f"""
    <section class="section">
      <div class="wrap">
        <h2>Prairie market snapshot (published aggregates)</h2>
        <p class="muted">Attributed to <a href="{market.get('source_url','https://www.machineryone.ca/market')}" rel="noopener">Machinery One’s public market page</a>. Dealer asking prices, not sale prices. PrairieComps does not scrape their listing inventory.</p>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Province</th><th>Listings tracked</th><th>Median ask</th><th>Range</th></tr></thead>
            <tbody>
              {''.join(market_bits)}
            </tbody>
          </table>
        </div>
      </div>
    </section>"""

    home_body = f"""
    <section class="hero">
      <div class="wrap">
        <div class="hero-card">
          <div class="badge">Alberta &amp; Prairies · Free MVP</div>
          <h1>Used farm &amp; heavy equipment asking prices you can trust</h1>
          <p class="lead">Search make/model comps built from public Alberta dealer listings. See median, low, and high asking prices — with links back to the source.</p>
          <div class="stats">
            <div class="stat"><div class="n">{len(listings)}</div><div class="l">Listings in dataset</div></div>
            <div class="stat"><div class="n">{len(top)}</div><div class="l">Model pages</div></div>
            <div class="stat"><div class="n">{money(overall_med)}</div><div class="l">Overall median ask</div></div>
            <div class="stat"><div class="n">{len(makes)}</div><div class="l">Makes covered</div></div>
          </div>
          <div class="filters" role="search">
            <input id="q" type="search" placeholder="Search make or model (e.g. John Deere 8R)" aria-label="Search make or model" />
            <select id="make" aria-label="Filter by make"><option value="">All makes</option>{make_opts}</select>
            <select id="province" aria-label="Filter by province"><option value="">All provinces</option>{prov_opts}</select>
            <button class="btn secondary" type="button" onclick="document.getElementById('q').value='';document.getElementById('make').value='';document.getElementById('province').value='';document.getElementById('q').dispatchEvent(new Event('input'))">Reset</button>
          </div>
          <p class="muted" style="margin:.75rem 0 0">Data refreshed {collected or 'recently'}. Asking prices only — not appraisals.</p>
        </div>
      </div>
    </section>
    <section class="section">
      <div class="wrap">
        <h2>Browse models</h2>
        <div class="grid" id="model-grid">
          {''.join(cards)}
        </div>
        <p id="empty-state" class="muted hidden">No models match those filters.</p>
      </div>
    </section>
    {market_html}
"""
    write(
        SITE / "index.html",
        layout(
            "PrairieComps — Used farm equipment prices in Alberta & the Prairies",
            home_body,
            active="home",
            description="Free asking-price comps for used farm and heavy equipment in Alberta and the Prairies.",
        ),
    )

    # Model pages
    for name, rows in top:
        st = model_stats(rows)
        slug = slugify(name)
        title = f"{name} used prices in Alberta | PrairieComps"
        if st["provinces"] == ["AB"]:
            seo_h1 = f"{name} used prices in Alberta"
        else:
            seo_h1 = f"{name} used prices on the Prairies"
        rows_sorted = sorted(rows, key=lambda r: (r.get("price_cad") is None, r.get("price_cad") or 0))
        trs = []
        for r in rows_sorted:
            hrs = f"{r['hours']:,}" if r.get("hours") is not None else "—"
            trs.append(
                f"<tr><td>{r.get('year') or '—'}</td><td>{hrs}</td><td>{money(r.get('price_cad'))}</td>"
                f"<td>{r.get('location') or '—'}</td><td>{r.get('source')}</td>"
                f"<td><a href=\"{r.get('source_url')}\" rel=\"noopener nofollow\" target=\"_blank\">View listing</a></td></tr>"
            )
        hours_txt = (
            f"{st['hours_min']:,} – {st['hours_max']:,} hrs"
            if st["hours_min"] is not None
            else "Hours not always listed"
        )
        body = f"""
    <section class="page-head">
      <div class="wrap">
        <div class="breadcrumbs"><a href="../index.html">Home</a> / Models / {name}</div>
        <h1>{seo_h1}</h1>
        <p class="lead">Asking-price comps from public Prairie dealer listings. Not an appraisal.</p>
        <div class="stats">
          <div class="stat"><div class="n">{money(st['median'])}</div><div class="l">Median ask (CAD)</div></div>
          <div class="stat"><div class="n">{money(st['low'])}</div><div class="l">Low ask</div></div>
          <div class="stat"><div class="n">{money(st['high'])}</div><div class="l">High ask</div></div>
          <div class="stat"><div class="n">{st['count']}</div><div class="l">Listings · {hours_txt}</div></div>
        </div>
        <div class="callout">These figures are dealer <strong>asking prices</strong> observed in public listings. Final negotiated prices differ. Confirm hours, options, and condition with the seller.</div>
      </div>
    </section>
    <section class="section">
      <div class="wrap">
        <h2>Current listings</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Year</th><th>Hours</th><th>Ask (CAD)</th><th>Location</th><th>Source</th><th>Link</th></tr></thead>
            <tbody>
              {''.join(trs)}
            </tbody>
          </table>
        </div>
      </div>
    </section>
"""
        # Model pages live under /models/ so fix asset paths
        html = layout(title, body, description=f"Used {name} asking prices in Alberta and the Prairies — median, low, high, hours, and listing links.")
        html = html.replace('href="css/', 'href="../css/').replace('href="js/', 'href="../js/').replace('src="js/', 'src="../js/')
        html = html.replace('href="index.html"', 'href="../index.html"')
        html = html.replace('href="for-dealers.html"', 'href="../for-dealers.html"')
        html = html.replace('href="about.html"', 'href="../about.html"')
        write(SITE / "models" / f"{slug}.html", html)

    # For Dealers
    dealers_body = f"""
    <section class="page-head">
      <div class="wrap">
        <div class="badge">Dealer revenue · CAD</div>
        <h1>Get found by serious Prairie equipment buyers</h1>
        <p class="lead">PrairieComps is free for buyers. Dealers can claim a page and buy Featured placement so your inventory shows up first on high-intent model searches.</p>
      </div>
    </section>
    <section class="section">
      <div class="wrap">
        <div class="tiers">
          <div class="tier">
            <h3>Featured</h3>
            <div class="price">$99<span class="muted">/mo CAD</span></div>
            <ul>
              <li>Featured badge on matching model pages</li>
              <li>Up to 25 highlighted listings</li>
              <li>Dealer name + link on comps</li>
              <li>Monthly performance snapshot (email)</li>
            </ul>
            <a class="mailto" href="mailto:{CONTACT_EMAIL}?subject=PrairieComps%20Featured%20%2499%2Fmo%20interest&body=Hi%20PrairieComps%2C%0A%0AI%27m%20interested%20in%20Featured%20placement%20(%2499%20CAD%2Fmo).%0A%0ADealership%3A%0ACity%2FProvince%3A%0AWebsite%3A%0AContact%20name%3A%0APhone%3A%0A">Email interest — Featured</a>
          </div>
          <div class="tier">
            <h3>Premium</h3>
            <div class="price">$199<span class="muted">/mo CAD</span></div>
            <ul>
              <li>Everything in Featured</li>
              <li>Claimed dealer page on PrairieComps</li>
              <li>Priority placement across top models</li>
              <li>Up to 75 highlighted listings</li>
              <li>Early access to B2B data exports (later)</li>
            </ul>
            <a class="mailto" href="mailto:{CONTACT_EMAIL}?subject=PrairieComps%20Premium%20%24199%2Fmo%20interest&body=Hi%20PrairieComps%2C%0A%0AI%27m%20interested%20in%20Premium%20placement%20(%24199%20CAD%2Fmo).%0A%0ADealership%3A%0ACity%2FProvince%3A%0AWebsite%3A%0AContact%20name%3A%0APhone%3A%0A">Email interest — Premium</a>
          </div>
        </div>
        <div class="callout" style="margin-top:1.25rem">
          No account required for now — use the mailto buttons above. We’ll follow up manually. Billing &amp; self-serve claiming come later.
        </div>
      </div>
    </section>
"""
    write(SITE / "for-dealers.html", layout("For Dealers — PrairieComps Featured placement", dealers_body, active="dealers"))

    # About
    about_body = f"""
    <section class="page-head">
      <div class="wrap prose">
        <h1>About PrairieComps</h1>
        <p>PrairieComps is a free website showing fair-market <strong>asking prices</strong> for used farm and heavy equipment across Alberta and the Canadian Prairies. It’s built for farmers, contractors, and dealers who want comps by make, model, year, and hours — without a paywall.</p>
        <h2>How we get prices</h2>
        <p>We collect publicly posted dealer inventory pages only when robots.txt and published terms allow it. Every listing in our dataset keeps a source URL and the date we saw it. We also cite publicly published market aggregates (with attribution) where useful.</p>
        <p>See <code>docs/SOURCES.md</code> in the project for the full allow/deny table.</p>
        <h2>What PrairieComps is not</h2>
        <ul>
          <li>Not an appraisal, valuation opinion, or lending guide</li>
          <li>Not auction hammer prices (unless a future permitted auction source is added)</li>
          <li>Not affiliated with John Deere, CLAAS, Case IH, Caterpillar, Ritchie Bros, or any OEM</li>
        </ul>
        <h2>Business model</h2>
        <p>Buyers use the site free. Later, dealers can pay <strong>$99–$199 CAD/mo</strong> for Featured / Premium placement and claimed dealer pages. B2B data products are on the roadmap.</p>
        <h2>Who’s behind it</h2>
        <p>Built for Phillip Herrod in Red Deer, Alberta. Contact: <a href="mailto:{GENERAL_EMAIL}">{GENERAL_EMAIL}</a> (placeholder).</p>
        <div class="callout">Disclaimer: prices are asking prices from public listings and may be incomplete, outdated, or wrong. Confirm every detail with the seller and inspect the machine before you buy.</div>
      </div>
    </section>
"""
    write(SITE / "about.html", layout("About PrairieComps", about_body, active="about"))

    # Simple robots.txt + sitemap for the static site itself
    model_urls = "\n".join(f"  <url><loc>/models/{slugify(name)}.html</loc></url>" for name, _ in top)
    write(
        SITE / "robots.txt",
        "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n",
    )
    write(
        SITE / "sitemap.xml",
        f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>/index.html</loc></url>
  <url><loc>/for-dealers.html</loc></url>
  <url><loc>/about.html</loc></url>
{model_urls}
</urlset>
""",
    )

    print(f"Built site with {len(listings)} listings, {len(top)} model pages → {SITE}")


if __name__ == "__main__":
    main()
