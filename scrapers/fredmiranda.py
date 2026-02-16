"""Fred Miranda Buy/Sell forum scraper."""

import re
import logging
from urllib.parse import quote_plus

from .base import BaseScraper, SearchResult, parse_price

logger = logging.getLogger(__name__)


class FredMirandaScraper(BaseScraper):
    name = "Fred Miranda Buy/Sell"
    key = "fredmiranda"
    base_url = "https://www.fredmiranda.com/forum/board/10"

    def get_search_url(self, query: str) -> str:
        return (
            f"https://www.fredmiranda.com/forum/board/10"
            f"?search={quote_plus(query)}"
        )

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        url = self.get_search_url(query)
        soup = self._get_soup(url)
        results = []

        # Fred Miranda forum threads are in table rows or list items
        # Look for thread links that contain selling tags
        thread_links = []

        # Try finding thread rows in the forum table
        rows = soup.select('tr, .row, .thread-row, [class*="thread"]')
        for row in rows:
            links = row.select('a[href*="/forum/topic/"]')
            for link in links:
                text = link.get_text(strip=True)
                if not text:
                    continue
                # Include posts with selling tags or all posts if they match query
                text_upper = text.upper()
                has_sell_tag = any(tag in text_upper for tag in ['[S]', '[FS]', '(S)', '(FS)'])
                if has_sell_tag or any(word.lower() in text.lower() for word in query.split()):
                    thread_links.append((text, link.get('href', '')))

        if not thread_links:
            # Broader search: all links to topics
            for link in soup.select('a[href*="/forum/topic/"]'):
                text = link.get_text(strip=True)
                if text and len(text) > 5:
                    thread_links.append((text, link.get('href', '')))

        seen_urls = set()
        for title, href in thread_links:
            if href in seen_urls:
                continue
            seen_urls.add(href)

            full_url = href if href.startswith('http') else f"https://www.fredmiranda.com{href}"
            price_str, price_num = parse_price(title)

            results.append(SearchResult(
                title=title,
                price=price_str,
                price_numeric=price_num,
                condition=None,
                url=full_url,
                site=self.name,
            ))

            if len(results) >= max_results:
                break

        return results
