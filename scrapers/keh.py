"""KEH Camera scraper."""

import logging
from urllib.parse import quote_plus

from .base import BaseScraper, SearchResult, parse_price

logger = logging.getLogger(__name__)


class KEHScraper(BaseScraper):
    name = "KEH Camera"
    key = "keh"
    base_url = "https://www.keh.com"

    def get_search_url(self, query: str) -> str:
        return f"https://www.keh.com/shop?s={quote_plus(query)}"

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        # KEH uses an Algolia-style search API internally.
        # Try the search page and parse results from the HTML.
        url = self.get_search_url(query)
        soup = self._get_soup(url)
        results = []

        # KEH renders product cards in their search results
        product_cards = soup.select('.product-card, .product-item, [data-product]')

        if not product_cards:
            # Fallback: try to find any product links with prices
            product_cards = soup.select('.product-list-item, .search-result-item, .product')

        if not product_cards:
            # Last resort: look for structured product data in the page
            # Try parsing product links that contain /shop/ in href
            links = soup.find_all('a', href=True)
            seen_urls = set()
            for link in links:
                href = link['href']
                if '/shop/' not in href or href in seen_urls:
                    continue
                # Skip navigation/category links
                text = link.get_text(strip=True)
                if not text or len(text) < 5:
                    continue
                if query.split()[0].lower() not in text.lower():
                    continue

                seen_urls.add(href)
                full_url = href if href.startswith('http') else f"https://www.keh.com{href}"

                # Try to find price near this link
                parent = link.find_parent(['div', 'li', 'article'])
                price_str, price_num = None, None
                condition = None
                if parent:
                    price_el = parent.select_one('.price, [class*="price"], .product-price')
                    if price_el:
                        price_str, price_num = parse_price(price_el.get_text())
                    cond_el = parent.select_one('.condition, [class*="condition"], .product-grade, [class*="grade"]')
                    if cond_el:
                        condition = cond_el.get_text(strip=True)

                results.append(SearchResult(
                    title=text,
                    price=price_str,
                    price_numeric=price_num,
                    condition=condition,
                    url=full_url,
                    site=self.name,
                    shipping="Free shipping (orders $49+)",
                    tax="Collected at checkout",
                ))
                if len(results) >= max_results:
                    break
            return results

        for card in product_cards[:max_results]:
            # Extract title
            title_el = card.select_one('h2, h3, h4, .product-title, .product-name, [class*="title"], [class*="name"]')
            title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)[:100]

            # Extract URL
            link_el = card.select_one('a[href]') or card.find_parent('a')
            item_url = ""
            if link_el:
                href = link_el.get('href', '')
                item_url = href if href.startswith('http') else f"https://www.keh.com{href}"

            # Extract price
            price_el = card.select_one('.price, [class*="price"]')
            price_str, price_num = None, None
            if price_el:
                price_str, price_num = parse_price(price_el.get_text())

            # Extract condition grade
            condition = None
            cond_el = card.select_one('.condition, [class*="condition"], [class*="grade"]')
            if cond_el:
                condition = cond_el.get_text(strip=True)

            if title:
                results.append(SearchResult(
                    title=title,
                    price=price_str,
                    price_numeric=price_num,
                    condition=condition,
                    url=item_url,
                    site=self.name,
                    shipping="Free shipping (orders $49+)",
                    tax="Collected at checkout",
                ))

        return results
