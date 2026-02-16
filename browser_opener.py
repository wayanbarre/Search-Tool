"""Browser opener fallback for Gear Finder.

Opens search URLs directly in the default browser.
This module has no dependencies beyond the standard library,
so it works even if requests/beautifulsoup4 aren't installed.
"""

import webbrowser
import sys


def open_search_urls(urls: list[tuple[str, str]], delay: float = 0.3) -> None:
    """Open a list of (site_name, url) tuples in the default browser.

    Args:
        urls: List of (site_name, url) tuples.
        delay: Seconds to wait between opening tabs (to avoid overwhelming the browser).
    """
    import time

    for site_name, url in urls:
        print(f"  Opening {site_name}: {url}")
        webbrowser.open(url)
        if delay > 0 and url != urls[-1][1]:
            time.sleep(delay)

    print(f"\nOpened {len(urls)} browser tab(s).")
