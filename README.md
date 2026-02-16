# Gear Finder

CLI tool that searches multiple used camera gear marketplaces simultaneously and returns aggregated results.

## Supported Sites

| Key            | Site                    | Notes                              |
|----------------|-------------------------|------------------------------------|
| `keh`          | KEH Camera              | Largest US used camera store       |
| `mpb`          | MPB                     | Global platform, condition ratings |
| `fredmiranda`  | Fred Miranda Buy/Sell   | Community forum, [S]/[FS] tags     |
| `usedphotopro` | UsedPhotoPro            | Roberts Camera, Shopify-based      |
| `reddit`       | Reddit r/photomarket    | JSON API, [S] selling posts        |
| `gearfocus`    | GearFocus               | Creator-to-creator marketplace     |
| `adorama`      | Adorama Used            | Condition grades E+ through X      |
| `bhphoto`      | B&H Photo Used          | 90-day warranty                    |
| `lensrentals`  | LensRentals             | Ex-rental pro gear                 |

## Installation

### Local (Python)

```bash
pip install -r requirements.txt
```

### Docker

```bash
docker compose build
```

## Usage

### Local

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

### Docker

```bash
# Search all sites
docker compose run --rm gear-finder "Sony 24-70 GM II"

# Search specific sites
docker compose run --rm gear-finder "Leica M11-P" --sites keh mpb

# JSON output
docker compose run --rm gear-finder "Sony 70-200 GM II" --json

# List sites
docker compose run --rm gear-finder --list-sites
```

Note: `--open` and `--browse-only` are not available inside Docker containers since there is no browser.

## Output Example

```
Searching 9 sites for: Sony 24-70 GM II

--- KEH Camera (3 results) ---

  Sony FE 24-70mm f/2.8 GM II  —  $1,549  (EX+)
  https://www.keh.com/shop/sony-fe-24-70mm-...

  Sony FE 24-70mm f/2.8 GM II  —  $1,449  (BGN)
  https://www.keh.com/shop/sony-fe-24-70mm-...

--- MPB (2 results) ---

  Sony FE 24-70mm f/2.8 GM II  —  $1,499  (Excellent)
  https://www.mpb.com/en-us/product/...

--- Reddit r/photomarket (1 result) ---

  [S] Sony 24-70 GM II - mint, box  —  $1,400  [2025-01-15]
  https://www.reddit.com/r/photomarket/...

Found 14 total results across 7 sites in 4.2s
No results on: LensRentals, GearFocus
```

## Architecture

```
gear-finder/
  gear_finder.py          # Main CLI entry point
  scrapers/
    __init__.py
    base.py               # Base scraper class + SearchResult dataclass
    keh.py                # KEH Camera
    mpb.py                # MPB
    fredmiranda.py        # Fred Miranda Buy/Sell
    usedphotopro.py       # UsedPhotoPro (Shopify)
    reddit.py             # Reddit r/photomarket (JSON API)
    gearfocus.py          # GearFocus
    adorama.py            # Adorama Used
    bhphoto.py            # B&H Photo Used
    lensrentals.py        # LensRentals Buy
  browser_opener.py       # Browser tab opener fallback
  requirements.txt
  Dockerfile
  docker-compose.yml
```

All scrapers run in parallel using `concurrent.futures.ThreadPoolExecutor`. Each site has a 15-second timeout. If a scraper fails (site redesigned, down, etc.), it reports the error and continues with the others.

## Notes

- No Selenium or headless browsers — scraping uses `requests` + `BeautifulSoup` only
- `--browse-only` works with zero dependencies (stdlib `webbrowser` module)
- Scrapers may break as sites update their HTML/APIs — the tool degrades gracefully
- Reddit scraper uses the public JSON API (no auth required)
- UsedPhotoPro uses Shopify's JSON search endpoint
