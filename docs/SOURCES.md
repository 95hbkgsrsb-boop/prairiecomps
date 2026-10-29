# PrairieComps data sources

Checked on 2026-10-29 (America/Edmonton). Collection only from sources that permit it via robots.txt and do not clearly prohibit automated collection / commercial reuse in published terms. No login, captcha, or robots bypass.

| Source | Type | robots.txt | Terms / access | Decision | Notes |
|--------|------|------------|----------------|----------|-------|
| Alberta AG Centre (ab-ag.ca) | AB dealer inventory | Allows `/` (Yoast); listings sitemap public | Terms page has no scrape ban found; public inventory | **USE** | Primary listing source. Polite crawl via sitemap + listing pages. |
| Western Tractor (westerntractor.ca) | AB John Deere dealer | robots.txt is Sitemap-only (allow-all) | Privacy page has no scrape ban found | **USE** | Used-equipment page HTML contains make/model/year/hours/price CAD. |
| Machinery One (machineryone.ca) `/market` | Published Canadian market aggregates | Allow `/` except `/go/`, `/results`, `/*?`, etc. | Terms: **no bulk copy/scrape**; market figures are general info | **AGGREGATES ONLY** | Cite published province/brand medians with attribution. Do **not** scrape `/browse` listings. |
| Machinery One listing/browse pages | Aggregated dealer listings | Browse allowed; `/go/` disallowed | Explicit scrape ban in terms | **EXCLUDE** | Competitor aggregator; ToS forbids scraping. |
| AgDealer (agdealer.com) | Marketplace | Partial allow; crawl-delay 10; `/api/` disallowed | License is personal non-commercial; reproduction/commercial use restricted | **EXCLUDE** | Also returns HTTP 403 to this box. |
| TractorHouse (tractorhouse.com) | Marketplace | Listing paths largely allowed | Cloudflare interstitial / bot challenge | **EXCLUDE** | Do not bypass captcha/challenge. |
| Kijiji (kijiji.ca) | Classifieds | Category browse allowed; many query params disallowed | Commercial reuse / bulk copy typically restricted; help ToS not reliably fetched | **EXCLUDE** | Not suitable for commercial comps site without permission. |
| Ritchie Bros / IronPlanet | Auction | Search often disallowed; some PDP allows | This box received HTTP 403 / Access Forbidden | **EXCLUDE** | Blocked; do not bypass. |
| Finning used.finning.com | Used Cat inventory | Content-Signal / CF managed | Captcha.eu / JS app; no usable static listings | **EXCLUDE** | No captcha bypass. |
| Brandt (brandt.ca) Used Equipment | Multi-province dealer | Allow-all robots | Search UI is ASP.NET postback; no usable static result list without interactive filter | **SKIP (MVP)** | Revisit with polite interactive crawl if terms OK. |
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
