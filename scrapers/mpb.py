"""MPB scraper."""

import json
import logging
from urllib.parse import quote_plus

from .base import BaseScraper, SearchResult, parse_price

logger = logging.getLogger(__name__)


class MPBScraper(BaseScraper):
    name = "MPB"
    key = "mpb"
    base_url = "https://www.mpb.com"

    def get_search_url(self, query: str) -> str:
        return f"https://www.mpb.com/en-us/search?q={quote_plus(query)}"

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        url = self.get_search_url(query)
        soup = self._get_soup(url)
        results = []

        # MPB may embed product data in JSON-LD or Next.js data
        # Check for JSON-LD structured data first
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'ItemList':
                    for item in data.get('itemListElement', [])[:max_results]:
                        product = item.get('item', item)
                        title = product.get('name', '')
                        item_url = product.get('url', '')
                        offers = product.get('offers', {})
                        price_str = None
                        price_num = None
                        if offers:
                            p = offers.get('price') or offers.get('lowPrice')
                            if p:
                                price_num = float(p)
                                price_str = f"${price_num:,.2f}"
                        results.append(SearchResult(
                            title=title,
                            price=price_str,
                            price_numeric=price_num,
                            condition=None,
                            url=item_url if item_url.startswith('http') else f"https://www.mpb.com{item_url}",
                            site=self.name,
                            shipping="Free shipping",
                            tax="Collected at checkout",
                        ))
                    if results:
                        return results[:max_results]
            except (json.JSONDecodeError, ValueError, TypeError):
                continue

        # Check for __NEXT_DATA__ (Next.js apps)
        next_data_script = soup.select_one('script#__NEXT_DATA__')
        if next_data_script:
            try:
                next_data = json.loads(next_data_script.string)
                # Navigate through Next.js data structure to find products
                props = next_data.get('props', {}).get('pageProps', {})
                products = (
                    props.get('products')
                    or props.get('searchResults', {}).get('products')
                    or props.get('results')
                    or []
                )
                if isinstance(products, dict):
                    products = products.get('items', products.get('results', []))
                for product in products[:max_results]:
                    if isinstance(product, dict):
                        title = product.get('title') or product.get('name', '')
                        slug = product.get('slug') or product.get('url', '')
                        item_url = slug if slug.startswith('http') else f"https://www.mpb.com/en-us/product/{slug}"
                        price_num = product.get('price') or product.get('lowestPrice')
                        price_str = f"${float(price_num):,.2f}" if price_num else None
                        price_num = float(price_num) if price_num else None
                        condition = product.get('condition') or product.get('grade')
                        results.append(SearchResult(
                            title=title,
                            price=price_str,
                            price_numeric=price_num,
                            condition=condition,
                            url=item_url,
                            site=self.name,
                            shipping="Free shipping",
                            tax="Collected at checkout",
                        ))
                if results:
                    return results[:max_results]
            except (json.JSONDecodeError, ValueError, TypeError, KeyError):
                pass

        # Fallback: parse HTML product cards
        product_cards = soup.select(
            '[class*="ProductCard"], [class*="product-card"], '
            '[data-testid*="product"], [class*="search-result"]'
        )

        if not product_cards:
            # Broader fallback
            product_cards = soup.select('a[href*="/product/"], a[href*="/en-us/product/"]')

        for card in product_cards[:max_results]:
            title_el = card.select_one(
                'h2, h3, h4, [class*="title"], [class*="name"], '
                '[class*="Title"], [class*="Name"]'
            )
            title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)[:100]

            link_el = card if card.name == 'a' else card.select_one('a[href]')
            item_url = ""
            if link_el:
                href = link_el.get('href', '')
                item_url = href if href.startswith('http') else f"https://www.mpb.com{href}"

            price_el = card.select_one('[class*="price"], [class*="Price"]')
            price_str, price_num = None, None
            if price_el:
                price_str, price_num = parse_price(price_el.get_text())

            condition = None
            cond_el = card.select_one('[class*="condition"], [class*="Condition"], [class*="grade"], [class*="Grade"]')
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
                    shipping="Free shipping",
                    tax="Collected at checkout",
                ))

        return results[:max_results]
