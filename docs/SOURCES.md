# PrairieComps data sources

Checked on 2026-10-29 (America/Edmonton). Collection only from sources that permit it via robots.txt and do not clearly prohibit automated collection / commercial reuse in published terms. No login, captcha, or robots bypass.

| Source | Type | robots.txt | Terms / access | Decision | Notes |
|--------|------|------------|----------------|----------|-------|
| Alberta AG Centre (ab-ag.ca) | AB dealer inventory | Allows `/` (Yoast); listings sitemap public | Terms page has no scrape ban found; public inventory | **USE** | Primary AB listing source. Polite crawl via sitemap + listing pages. |
| Western Tractor (westerntractor.ca) | AB John Deere dealer | robots.txt is Sitemap-only (allow-all) | Privacy page has no scrape ban found | **USE** | Used-equipment page HTML contains make/model/year/hours/price CAD. |
| Full Line Ag (fulllineag.com) | SK AGCO / multi-brand dealer | Allows `/` except `/wp-admin/` | No terms/privacy scrape ban found (pages 404) | **USE** | Used-equipment list pages with Price / Engine Hours / Location in HTML. SK coverage. |
| Prairie Sales (prairiesales.ca) | MB farm equipment dealer | Allows `/` except `/wp-admin/`; listing sitemap public | No terms scrape ban found | **USE** | Listing sitemap + detail pages (Our Price, Year, Make, Model, Hours, Location). MB coverage. |
| Flaman Agriculture (flamanagriculture.com) | AB/SK farm inventory | Allows `/` (`Disallow: /region` only) | Privacy discusses log files only; no scrape ban | **USE** | Public `/inventory?type=used` cards with title, location, price. Mixed AB/SK locations. |
| Machinery One (machineryone.ca) `/market` | Published Canadian market aggregates | Allow `/` except `/go/`, `/results`, `/*?`, etc. | Terms: **no bulk copy/scrape**; market figures are general info | **AGGREGATES ONLY** | Cite published province/brand medians with attribution. Do **not** scrape `/browse` listings. |
| Machinery One listing/browse pages | Aggregated dealer listings | Browse allowed; `/go/` disallowed | Explicit scrape ban in terms | **EXCLUDE** | Competitor aggregator; ToS forbids scraping. |
| AgDealer (agdealer.com) | Marketplace | Partial allow; crawl-delay 10; `/api/` disallowed | License is personal non-commercial; reproduction/commercial use restricted | **EXCLUDE** | Also returns HTTP 403 to this box. |
| TractorHouse (tractorhouse.com) | Marketplace | Listing paths largely allowed | Cloudflare interstitial / bot challenge | **EXCLUDE** | Do not bypass captcha/challenge. |
| Kijiji (kijiji.ca) | Classifieds | Category browse allowed; many query params disallowed | Commercial reuse / bulk copy typically restricted | **EXCLUDE** | Not suitable for commercial comps site without permission. |
| Ritchie Bros / IronPlanet | Auction | Search often disallowed; some PDP allows | This box received HTTP 403 / Access Forbidden | **EXCLUDE** | Blocked; do not bypass. |
| Finning used.finning.com | Used Cat inventory | Content-Signal / CF managed | Captcha.eu / JS app; no usable static listings | **EXCLUDE** | No captcha bypass. |
| Brandt (brandt.ca) Used Equipment | Multi-province dealer | Allow-all robots | Search UI is ASP.NET postback; no usable static result list without interactive filter | **SKIP** | Revisit with polite interactive crawl if terms OK. |
| Rocky Mountain Equipment (rockymtn.com / rockymountainequipment.com) | Multi-province JD dealer | robots allow inventory paths | Sucuri / Cloudflare challenge (403) from this box | **EXCLUDE** | Blocked; do not bypass. |
| Cervus Equipment / more.brandt.ca | JD dealer (now Brandt) | Partial allow | Cloudflare challenge | **EXCLUDE** | Blocked; do not bypass. |
| Redhead Equipment (redheadequipment.ca) | SK dealer | — | Cloudflare bot challenge | **EXCLUDE** | Do not bypass. |
| Canada West Harvest Centre (cawhc.com) | SK dealer | Captcha gate on robots/inventory | SiteGround captcha | **EXCLUDE** | Do not bypass. |
| Mazergroup (mazergroup.ca) | SK/MB dealer | Content-Signal `search=yes,use=reference` | Inventory showroom is MyDealer JS app (no static prices) | **SKIP** | JS-gated inventory; no captcha bypass / API scrape. |
| South Country Equipment (southcountry.ca) | SK JD dealer | Content-Signal `search=yes,use=reference` | Inventory showroom JS-gated | **SKIP** | Same MyDealer pattern. |
| Horizon Ag & Turf / agland.ca | AB JD dealer | — | MyDealer JS inventory; no prices in static HTML | **SKIP** | JS-gated. |
| Palliser Sales (pallisersales.com) | AB AGCO/Kubota dealer | — | HTTP 400 from this box | **EXCLUDE** | Access failure; do not work around. |
| Agriterra (agriterraeq.com) | AB AGCO dealer | — | Bot interstitial (“One moment, please…”) | **EXCLUDE** | Do not bypass. |
| Triag Implements (triag.ca) | AB dealer | Allows most paths | Pre-owned page embeds IronSearch iframe; no static prices | **SKIP** | No usable static inventory. |
| Webb’s Machinery (webbsmachinery.com) | AB New Holland | robots present | Pre-owned page has no usable priced static cards from this box | **SKIP** | Insufficient static data. |
| Strongco / Nors Construction | Heavy equipment | Redirects / brand sites | No usable static used list found | **SKIP** | Revisit later. |
| Ag-Plus (agplus.ca) | AB dealer | Partial allow | HTTP 403 on inventory URLs from this box | **EXCLUDE** | Blocked. |
| Hanlon Ag (hanlonag.com) | AB dealer | robots request 400 | HTTP 400 from this box | **EXCLUDE** | Access failure; do not work around. |
| Lewis.ca | Dealer | `Disallow: /` for `*` | N/A | **EXCLUDE** | robots forbids. |
| Farms.com classifieds | Classifieds | Disallows `/canada/`, `/classifides/`, etc. | — | **EXCLUDE** | Relevant paths disallowed. |

## Collection policy

- User-Agent: `PrairieCompsBot/0.1 (+https://prairiecomps.local; research)`
- Delay ≥ 1.5s between listing requests
- Stop on HTTP 403/401/captcha; record and skip
- Store `source_url` and `date_seen` on every row
- Prices are **asking prices**, not sale prices or appraisals
- Obviously bad prices (e.g. a $1,800 combine) are flagged `outlier` and excluded from medians while still shown on model pages
