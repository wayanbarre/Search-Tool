# Gear Finder

Search multiple used camera gear marketplaces simultaneously. Comes with a **web UI** and a **CLI** — deploy on your NAS via Docker.

## Supported Sites

| Key            | Site                    | Shipping                     | Notes                              |
|----------------|-------------------------|------------------------------|------------------------------------|
| `keh`          | KEH Camera              | Free (orders $49+)           | Largest US used camera store       |
| `mpb`          | MPB                     | Free                         | Global platform, condition ratings |
| `fredmiranda`  | Fred Miranda Buy/Sell   | Varies (peer-to-peer)        | Community forum, [S]/[FS] tags     |
| `usedphotopro` | UsedPhotoPro            | Free (orders $99+)           | Roberts Camera, Shopify-based      |
| `reddit`       | Reddit r/photomarket    | Varies (peer-to-peer)        | JSON API, [S] selling posts        |
| `gearfocus`    | GearFocus               | Set by seller                | Creator-to-creator marketplace     |
| `adorama`      | Adorama Used            | Free standard                | Condition grades E+ through X      |
| `bhphoto`      | B&H Photo Used          | Free                         | 90-day warranty                    |
| `lensrentals`  | LensRentals             | Calculated at checkout       | Ex-rental pro gear                 |

## Quick Start (Docker on NAS)

```bash
git clone <repo-url> && cd gear-finder
docker compose up -d
```

Open **http://your-nas-ip:5000** in a browser. That's it.

## Installation

### Docker (recommended for NAS)

```bash
docker compose build
docker compose up -d          # Web UI on port 5000
```

### Local (Python)

```bash
pip install -r requirements.txt
python web_app.py             # Web UI at http://localhost:5000
```

## Usage

### Web UI

Navigate to `http://localhost:5000` (or your NAS IP). Type a search query, optionally filter by site, and click Search. Each result shows:

- **Price** — listing price
- **Condition** — site-specific grade (EX+, Like New, etc.)
- **Shipping** — free shipping, calculated, varies by seller
- **Tax** — collected at checkout (US sales tax) or N/A for peer-to-peer

Click any result to go directly to the listing on the source website.

### Web API

```
GET /api/search?q=Sony+24-70+GM+II&sites=keh,mpb&max=5
```

Returns JSON for scripting/integration.

### CLI

```bash
# Search all sites
python gear_finder.py "Sony 24-70 GM II"

# Search specific sites only
python gear_finder.py "Leica M11-P" --sites keh mpb fredmiranda

# Open all search result pages in browser
python gear_finder.py "Sony A1" --open

# Just open browser tabs, skip scraping
python gear_finder.py "Canon RF 35mm 1.4" --browse-only

# Output as JSON (for piping/scripting)
python gear_finder.py "Sony 70-200 GM II" --json

# List all supported sites
python gear_finder.py --list-sites

# Set max results per site
python gear_finder.py "Fuji X100VI" --max 5
```

### Docker CLI

```bash
# Ad-hoc CLI searches (uses the "cli" profile)
docker compose run --rm gear-finder-cli "Sony 24-70 GM II"
docker compose run --rm gear-finder-cli "Leica M11-P" --sites keh mpb --json
docker compose run --rm gear-finder-cli --list-sites
```

## Architecture

```
gear-finder/
  gear_finder.py          # CLI entry point
  web_app.py              # Flask web UI + JSON API
  templates/
    index.html            # Search page (dark theme, responsive)
  scrapers/
    __init__.py
    base.py               # BaseScraper + SearchResult dataclass
    keh.py                # KEH Camera
    mpb.py                # MPB
    fredmiranda.py        # Fred Miranda Buy/Sell
    usedphotopro.py       # UsedPhotoPro (Shopify)
    reddit.py             # Reddit r/photomarket (JSON API)
    gearfocus.py          # GearFocus
    adorama.py            # Adorama Used
    bhphoto.py            # B&H Photo Used
    lensrentals.py        # LensRentals Buy
  browser_opener.py       # Browser tab opener (CLI fallback)
  requirements.txt
  Dockerfile
  docker-compose.yaml
```

All scrapers run in parallel using `concurrent.futures.ThreadPoolExecutor`. Each site has a 15-second timeout. If a scraper fails, it reports the error and continues with the others.

## Notes

- No Selenium or headless browsers — uses `requests` + `BeautifulSoup` only
- Results include price, condition, shipping, and tax info per listing
- Each result is a direct link to the listing on the source site
- Scrapers may break as sites update their HTML/APIs — the tool degrades gracefully
- Reddit scraper uses the public JSON API (no auth required)
- UsedPhotoPro uses Shopify's JSON search endpoint
- Web UI uses a single-page dark theme, works on mobile
