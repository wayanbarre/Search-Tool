"""LensRentals (Buy) scraper."""

import logging
from urllib.parse import quote_plus

from .base import BaseScraper, SearchResult, parse_price

logger = logging.getLogger(__name__)


class LensRentalsScraper(BaseScraper):
    name = "LensRentals"
    key = "lensrentals"
    base_url = "https://www.lensrentals.com"
    # LensRentals buy section can be tricky to scrape directly
    browser_only = False

    def get_search_url(self, query: str) -> str:
        return f"https://www.lensrentals.com/buy/search?query={quote_plus(query)}"

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        url = self.get_search_url(query)
        results = []

        try:
            soup = self._get_soup(url)
        except Exception as e:
            logger.warning("LensRentals fetch failed: %s", e)
            return results

        # Look for product cards in the buy section
        product_cards = soup.select(
            '.product-card, .product-item, [class*="product"], '
            '.search-result, [class*="listing"], .item'
        )

        if not product_cards:
            # Try finding product links
            for link in soup.select('a[href*="/buy/"]'):
                text = link.get_text(strip=True)
                href = link.get('href', '')
                if not text or len(text) < 5 or '/buy/search' in href:
                    continue
                full_url = href if href.startswith('http') else f"https://www.lensrentals.com{href}"
                parent = link.find_parent(['div', 'li', 'article'])
                price_str, price_num = None, None
                if parent:
                    price_el = parent.select_one('[class*="price"], .price')
                    if price_el:
                        price_str, price_num = parse_price(price_el.get_text())
                results.append(SearchResult(
                    title=text,
                    price=price_str,
                    price_numeric=price_num,
                    condition="Ex-Rental",
                    url=full_url,
                    site=self.name,
                ))
                if len(results) >= max_results:
                    break
            return results

        for card in product_cards[:max_results]:
            title_el = card.select_one(
                'h2, h3, h4, [class*="title"], [class*="name"], '
                '[class*="Title"], [class*="Name"]'
            )
            title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)[:100]

            link_el = card.select_one('a[href]')
            item_url = ""
            if link_el:
                href = link_el.get('href', '')
                item_url = href if href.startswith('http') else f"https://www.lensrentals.com{href}"

            price_el = card.select_one('[class*="price"], [class*="Price"], .price')
            price_str, price_num = None, None
            if price_el:
                price_str, price_num = parse_price(price_el.get_text())

            if title and len(title) > 3:
                results.append(SearchResult(
                    title=title,
                    price=price_str,
                    price_numeric=price_num,
                    condition="Ex-Rental",
                    url=item_url,
                    site=self.name,
                ))

        return results[:max_results]
