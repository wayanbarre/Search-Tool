#!/usr/bin/env python3
"""Gear Finder — Search multiple used camera gear marketplaces simultaneously."""

import argparse
import json
import sys
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers import ALL_SCRAPERS, SearchResult


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s [%(name)s] %(message)s",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search multiple used camera gear marketplaces simultaneously.",
        epilog="Examples:\n"
               '  python gear_finder.py "Sony 24-70 GM II"\n'
               '  python gear_finder.py "Leica M11-P" --sites keh mpb fredmiranda\n'
               '  python gear_finder.py "Sony A1" --open\n'
               '  python gear_finder.py "Canon RF 35mm 1.4" --browse-only\n'
               '  python gear_finder.py "Sony 70-200 GM II" --json\n'
               '  python gear_finder.py --list-sites\n',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Search query (e.g., 'Sony 24-70 GM II')",
    )
    parser.add_argument(
        "--sites",
        nargs="+",
        metavar="SITE",
        help="Only search specific sites (use site keys, see --list-sites)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Also open all search result pages in the default browser",
    )
    parser.add_argument(
        "--browse-only",
        action="store_true",
        help="Just open browser tabs for each site's search page (skip scraping)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--list-sites",
        action="store_true",
        help="List all supported sites and exit",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=10,
        metavar="N",
        help="Maximum results per site (default: 10)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    return parser


def list_sites() -> None:
    print("Supported sites:\n")
    for scraper_cls in ALL_SCRAPERS:
        s = scraper_cls()
        tag = " (browser-only)" if s.browser_only else ""
        print(f"  {s.key:<16} {s.name}{tag}")
        print(f"  {'':<16} {s.base_url}")
        print()


def get_selected_scrapers(site_keys: list[str] | None) -> list:
    """Return scraper instances filtered by requested site keys."""
    all_instances = [cls() for cls in ALL_SCRAPERS]

    if not site_keys:
        return all_instances

    key_set = {k.lower() for k in site_keys}
    selected = [s for s in all_instances if s.key in key_set]

    unknown = key_set - {s.key for s in all_instances}
    if unknown:
        print(f"Warning: Unknown site(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        print(f"Use --list-sites to see available sites.", file=sys.stderr)

    return selected


def search_single(scraper, query: str, max_results: int) -> tuple[str, list[SearchResult], str | None]:
    """Search a single site. Returns (site_name, results, error_message)."""
    try:
        if scraper.browser_only:
            return (scraper.name, [], None)
        results = scraper.search(query, max_results)
        return (scraper.name, results, None)
    except Exception as e:
        return (scraper.name, [], str(e))


def run_search(scrapers, query: str, max_results: int) -> dict:
    """Run search across all scrapers in parallel.

    Returns dict with keys: results_by_site, errors, no_results, elapsed.
    """
    results_by_site = {}
    errors = {}
    no_results = []

    start = time.time()

    with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
        futures = {
            executor.submit(search_single, s, query, max_results): s
            for s in scrapers
        }

        for future in as_completed(futures):
            site_name, results, error = future.result()
            if error:
                errors[site_name] = error
            elif results:
                results_by_site[site_name] = results
            else:
                no_results.append(site_name)

    elapsed = time.time() - start

    return {
        "results_by_site": results_by_site,
        "errors": errors,
        "no_results": no_results,
        "elapsed": elapsed,
    }


def print_results(data: dict, query: str, total_sites: int) -> None:
    """Print results in the human-readable terminal format."""
    results_by_site = data["results_by_site"]
    errors = data["errors"]
    no_results = data["no_results"]
    elapsed = data["elapsed"]

    total_results = sum(len(r) for r in results_by_site.values())

    print(f"\nSearching {total_sites} sites for: {query}\n")

    # Maintain the order from ALL_SCRAPERS
    ordered_names = [cls().name for cls in ALL_SCRAPERS]

    for site_name in ordered_names:
        if site_name not in results_by_site:
            continue
        results = results_by_site[site_name]
        print(f"--- {site_name} ({len(results)} result{'s' if len(results) != 1 else ''}) ---\n")
        for r in results:
            parts = [f"  {r.title}"]
            meta = []
            if r.price:
                meta.append(r.price)
            if r.condition:
                meta.append(f"({r.condition})")
            if r.posted_date:
                meta.append(f"[{r.posted_date}]")
            if meta:
                parts.append("  —  " + "  ".join(meta))
            print("".join(parts))
            print(f"  {r.url}\n")

    # Summary line
    sites_with_results = len(results_by_site)
    print(f"Found {total_results} total results across {sites_with_results} sites in {elapsed:.1f}s")

    if no_results:
        print(f"No results on: {', '.join(sorted(no_results))}")

    if errors:
        print(f"Errors on: {', '.join(sorted(errors.keys()))}")
        for site, err in sorted(errors.items()):
            print(f"  {site}: {err}", file=sys.stderr)


def print_json(data: dict, query: str) -> None:
    """Print results as JSON."""
    output = {
        "query": query,
        "results": {},
        "errors": data["errors"],
        "no_results": data["no_results"],
        "elapsed_seconds": round(data["elapsed"], 2),
    }

    for site_name, results in data["results_by_site"].items():
        output["results"][site_name] = [
            {
                "title": r.title,
                "price": r.price,
                "price_numeric": r.price_numeric,
                "condition": r.condition,
                "url": r.url,
                "posted_date": r.posted_date,
            }
            for r in results
        ]

    print(json.dumps(output, indent=2))


def handle_browse_only(scrapers, query: str) -> None:
    """Open browser tabs for all selected sites' search pages."""
    from browser_opener import open_search_urls

    urls = [(s.name, s.get_search_url(query)) for s in scrapers]
    print(f"Opening {len(urls)} search page(s) for: {query}\n")
    open_search_urls(urls)


def handle_open(data: dict) -> None:
    """Open result URLs in the browser after displaying results."""
    from browser_opener import open_search_urls

    urls = []
    for site_name, results in data["results_by_site"].items():
        for r in results:
            if r.url:
                urls.append((site_name, r.url))

    if urls:
        print(f"\nOpening {len(urls)} result(s) in browser...\n")
        open_search_urls(urls)
    else:
        print("\nNo result URLs to open.")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_sites:
        list_sites()
        return

    if not args.query:
        parser.print_help()
        sys.exit(1)

    setup_logging(args.verbose)
    scrapers = get_selected_scrapers(args.sites)

    if not scrapers:
        print("No matching sites found. Use --list-sites to see available sites.", file=sys.stderr)
        sys.exit(1)

    # Browse-only mode: just open tabs, no scraping
    if args.browse_only:
        handle_browse_only(scrapers, args.query)
        return

    # Run parallel search
    data = run_search(scrapers, args.query, args.max)

    # Output results
    if args.json_output:
        print_json(data, args.query)
    else:
        print_results(data, args.query, len(scrapers))

    # Open in browser if requested
    if args.open:
        handle_open(data)


if __name__ == "__main__":
    main()
