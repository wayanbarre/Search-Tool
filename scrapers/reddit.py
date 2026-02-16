"""Reddit r/photomarket scraper using the JSON API."""

import logging
from urllib.parse import quote_plus

from .base import BaseScraper, SearchResult, parse_price

logger = logging.getLogger(__name__)


class RedditScraper(BaseScraper):
    name = "Reddit r/photomarket"
    key = "reddit"
    base_url = "https://www.reddit.com/r/photomarket"

    def get_search_url(self, query: str) -> str:
        return (
            f"https://www.reddit.com/r/photomarket/search/"
            f"?q={quote_plus(query)}&restrict_sr=1&sort=new"
        )

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        url = (
            f"https://www.reddit.com/r/photomarket/search.json"
            f"?q={quote_plus(query)}&restrict_sr=1&sort=new&limit={max_results}"
        )
        # Reddit requires a unique User-Agent for API access
        headers = {
            "User-Agent": "GearFinder/1.0 (camera gear search tool)"
        }
        resp = self._get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            title = post.get("title", "")

            # Only include selling posts
            title_upper = title.upper()
            if "[S]" not in title_upper and "[FS]" not in title_upper:
                continue

            permalink = post.get("permalink", "")
            post_url = f"https://www.reddit.com{permalink}" if permalink else ""

            price_str, price_num = parse_price(title)

            # Try to get date
            created_utc = post.get("created_utc")
            posted_date = None
            if created_utc:
                from datetime import datetime, timezone
                dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                posted_date = dt.strftime("%Y-%m-%d")

            results.append(SearchResult(
                title=title.strip(),
                price=price_str,
                price_numeric=price_num,
                condition=None,
                url=post_url,
                site=self.name,
                posted_date=posted_date,
                shipping="Varies (peer-to-peer)",
                tax="Not applicable (peer-to-peer)",
            ))

            if len(results) >= max_results:
                break

        return results
