"""UsedPhotoPro (Roberts Camera) scraper — Shopify-based store."""

import json
import logging
from urllib.parse import quote_plus

from .base import BaseScraper, SearchResult

logger = logging.getLogger(__name__)


class UsedPhotoProScraper(BaseScraper):
    name = "UsedPhotoPro"
    key = "usedphotopro"
    base_url = "https://usedphotopro.com"

    def get_search_url(self, query: str) -> str:
        return f"https://usedphotopro.com/search?q={quote_plus(query)}"

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        # Shopify stores have a predictable JSON search endpoint
        json_url = (
            f"https://usedphotopro.com/search/suggest.json"
            f"?q={quote_plus(query)}&resources[type]=product"
            f"&resources[limit]={max_results}"
        )
        results = []

        try:
            data = self._get_json(json_url)
            products = (
                data.get('resources', {})
                .get('results', {})
                .get('products', [])
            )

            for product in products[:max_results]:
                title = product.get('title', '')
                handle = product.get('handle', '')
                item_url = f"https://usedphotopro.com/products/{handle}" if handle else product.get('url', '')
                if item_url and not item_url.startswith('http'):
                    item_url = f"https://usedphotopro.com{item_url}"

                price = product.get('price')
                price_str = None
                price_num = None
                if price:
                    # Shopify prices can be in cents or dollars depending on config
                    try:
                        p = float(price)
                        # If price seems to be in cents (> 10000), convert
                        if p > 10000:
                            p = p / 100.0
                        price_num = p
                        price_str = f"${p:,.2f}"
                    except (ValueError, TypeError):
                        from .base import parse_price
                        price_str, price_num = parse_price(str(price))

                # Try to extract condition from title or tags
                condition = None
                body = product.get('body', '') or ''
                for grade in ['Like New', 'LN', 'Excellent', 'EX+', 'EX', 'Very Good', 'VG', 'Good', 'BGN', 'Fair']:
                    if grade.lower() in title.lower() or grade.lower() in body.lower():
                        condition = grade
                        break

                results.append(SearchResult(
                    title=title,
                    price=price_str,
                    price_numeric=price_num,
                    condition=condition,
                    url=item_url,
                    site=self.name,
                    shipping="Free shipping (orders $99+)",
                    tax="Collected at checkout",
                ))

            return results

        except Exception:
            logger.debug("Shopify JSON endpoint failed, falling back to HTML scraping")

        # Fallback to HTML scraping
        html_url = self.get_search_url(query)
        soup = self._get_soup(html_url)

        product_cards = soup.select(
            '.product-card, .product-item, [class*="product"], '
            '.grid-item, .collection-product'
        )

        for card in product_cards[:max_results]:
            title_el = card.select_one('h2, h3, h4, .product-title, [class*="title"], a')
            title = title_el.get_text(strip=True) if title_el else ''

            link_el = card.select_one('a[href*="/products/"]')
            item_url = ""
            if link_el:
                href = link_el.get('href', '')
                item_url = href if href.startswith('http') else f"https://usedphotopro.com{href}"

            price_el = card.select_one('[class*="price"], .money')
            price_str, price_num = None, None
            if price_el:
                from .base import parse_price
                price_str, price_num = parse_price(price_el.get_text())

            if title:
                results.append(SearchResult(
                    title=title,
                    price=price_str,
                    price_numeric=price_num,
                    condition=None,
                    url=item_url,
                    site=self.name,
                    shipping="Free shipping (orders $99+)",
                    tax="Collected at checkout",
                ))

        return results[:max_results]
