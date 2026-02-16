"""Base scraper class and SearchResult dataclass for Gear Finder."""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 15


@dataclass
class SearchResult:
    title: str
    price: Optional[str]
    price_numeric: Optional[float]
    condition: Optional[str]
    url: str
    site: str
    posted_date: Optional[str] = None
    shipping: Optional[str] = None       # e.g. "Free Shipping", "$9.95", "Calculated at checkout"
    tax: Optional[str] = None            # e.g. "Tax included", "Collected at checkout"


def parse_price(text: str) -> tuple[Optional[str], Optional[float]]:
    """Extract price string and numeric value from text.

    Returns (price_display, price_numeric) tuple.
    """
    if not text:
        return None, None
    match = re.search(r'\$[\d,]+(?:\.\d{2})?', text)
    if match:
        price_str = match.group(0)
        numeric = float(price_str.replace('$', '').replace(',', ''))
        return price_str, numeric
    return None, None


class BaseScraper:
    name: str = "Base"
    key: str = "base"
    base_url: str = ""
    browser_only: bool = False

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        raise NotImplementedError

    def get_search_url(self, query: str) -> str:
        """Return the browser-friendly search URL for --open / --browse-only mode."""
        raise NotImplementedError

    def _get(self, url: str, **kwargs) -> requests.Response:
        """Perform a GET request with standard timeout and error handling."""
        kwargs.setdefault('timeout', REQUEST_TIMEOUT)
        return self.session.get(url, **kwargs)

    def _get_json(self, url: str, **kwargs) -> dict:
        """Perform a GET request and return parsed JSON."""
        resp = self._get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _get_soup(self, url: str, **kwargs):
        """Perform a GET request and return a BeautifulSoup object."""
        from bs4 import BeautifulSoup
        resp = self._get(url, **kwargs)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'lxml')
