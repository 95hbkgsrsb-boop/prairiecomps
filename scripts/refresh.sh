#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
./.venv/bin/python scripts/collect_listings.py
./.venv/bin/python scripts/build_site.py
echo "Refresh complete. Serve with: python3 -m http.server 8080 --directory site"
