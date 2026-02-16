"""B&H Photo Used scraper."""

import json
import logging
from urllib.parse import quote_plus

from .base import BaseScraper, SearchResult, parse_price

logger = logging.getLogger(__name__)


class BHPhotoScraper(BaseScraper):
    name = "B&H Photo Used"
    key = "bhphoto"
    base_url = "https://www.bhphotovideo.com"
    # B&H is complex; scraping may be unreliable
    browser_only = False

    def get_search_url(self, query: str) -> str:
        return (
            f"https://www.bhphotovideo.com/c/search?q={quote_plus(query)}"
            f"&filters=fct_condition_2187%3Aused"
        )

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        url = self.get_search_url(query)
        results = []

        try:
            soup = self._get_soup(url)
        except Exception as e:
            logger.warning("B&H Photo fetch failed: %s", e)
            return results

        # Check for JSON-LD structured data
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string)
                items = []
                if isinstance(data, dict) and data.get('@type') == 'ItemList':
                    items = data.get('itemListElement', [])
                elif isinstance(data, list):
                    items = data

                for item in items[:max_results]:
                    product = item.get('item', item) if isinstance(item, dict) else item
                    if not isinstance(product, dict):
                        continue
                    title = product.get('name', '')
                    item_url = product.get('url', '')
                    if item_url and not item_url.startswith('http'):
                        item_url = f"https://www.bhphotovideo.com{item_url}"
                    offers = product.get('offers', {})
                    price_str, price_num = None, None
                    if offers:
                        p = offers.get('price') or offers.get('lowPrice')
                        if p:
                            price_num = float(p)
                            price_str = f"${price_num:,.2f}"
                    if title:
                        results.append(SearchResult(
                            title=title,
                            price=price_str,
                            price_numeric=price_num,
                            condition="Used",
                            url=item_url,
                            site=self.name,
                            shipping="Free shipping",
                            tax="Collected at checkout",
                        ))
                if results:
                    return results[:max_results]
            except (json.JSONDecodeError, ValueError, TypeError):
                continue

        # Fallback: parse product cards from HTML
        product_cards = soup.select(
            '[data-selenium="miniProductPage"], .product-item, '
            '[class*="productCard"], [class*="product-card"]'
        )

        for card in product_cards[:max_results]:
            title_el = card.select_one(
                'h3, h4, [data-selenium="miniProductPageProductName"], '
                '[class*="title"], [class*="name"]'
            )
            title = title_el.get_text(strip=True) if title_el else ''

            link_el = card.select_one('a[href]')
            item_url = ""
            if link_el:
                href = link_el.get('href', '')
                item_url = href if href.startswith('http') else f"https://www.bhphotovideo.com{href}"

            price_el = card.select_one(
                '[data-selenium="pricingPrice"], [class*="price"], .price'
            )
            price_str, price_num = None, None
            if price_el:
                price_str, price_num = parse_price(price_el.get_text())

            if title:
                results.append(SearchResult(
                    title=title,
                    price=price_str,
                    price_numeric=price_num,
                    condition="Used",
                    url=item_url,
                    site=self.name,
                    shipping="Free shipping",
                    tax="Collected at checkout",
                ))

        return results[:max_results]
