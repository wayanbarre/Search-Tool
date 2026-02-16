"""GearFocus marketplace scraper."""

import logging
from urllib.parse import quote_plus

from .base import BaseScraper, SearchResult, parse_price

logger = logging.getLogger(__name__)


class GearFocusScraper(BaseScraper):
    name = "GearFocus"
    key = "gearfocus"
    base_url = "https://www.gearfocus.com"

    def get_search_url(self, query: str) -> str:
        return f"https://www.gearfocus.com/search?q={quote_plus(query)}"

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        url = self.get_search_url(query)
        soup = self._get_soup(url)
        results = []

        # Look for product cards/listings
        product_cards = soup.select(
            '.product-card, .listing-card, [class*="ProductCard"], '
            '[class*="product-item"], [class*="listing"], '
            '[class*="search-result"], .product'
        )

        if not product_cards:
            # Broader fallback: links that look like product pages
            for link in soup.select('a[href]'):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if not text or len(text) < 5:
                    continue
                # Look for product-like links
                if any(seg in href for seg in ['/listing/', '/product/', '/item/']):
                    full_url = href if href.startswith('http') else f"https://www.gearfocus.com{href}"
                    price_str, price_num = parse_price(text)
                    parent = link.find_parent(['div', 'li', 'article'])
                    if parent:
                        price_el = parent.select_one('[class*="price"], .price')
                        if price_el:
                            price_str, price_num = parse_price(price_el.get_text())
                    results.append(SearchResult(
                        title=text,
                        price=price_str,
                        price_numeric=price_num,
                        condition=None,
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
                item_url = href if href.startswith('http') else f"https://www.gearfocus.com{href}"

            price_el = card.select_one('[class*="price"], [class*="Price"], .price')
            price_str, price_num = None, None
            if price_el:
                price_str, price_num = parse_price(price_el.get_text())

            condition = None
            cond_el = card.select_one('[class*="condition"], [class*="Condition"]')
            if cond_el:
                condition = cond_el.get_text(strip=True)

            if title and len(title) > 3:
                results.append(SearchResult(
                    title=title,
                    price=price_str,
                    price_numeric=price_num,
                    condition=condition,
                    url=item_url,
                    site=self.name,
                ))

        return results[:max_results]
