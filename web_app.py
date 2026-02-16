#!/usr/bin/env python3
"""Gear Finder — Web interface for searching used camera gear marketplaces."""

import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

from flask import Flask, render_template, request, jsonify

from scrapers import ALL_SCRAPERS, SearchResult

app = Flask(__name__)

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Build scraper registry once
SCRAPER_REGISTRY = {cls().key: cls for cls in ALL_SCRAPERS}


def get_scrapers(site_keys=None):
    """Return scraper instances, optionally filtered by keys."""
    if site_keys:
        key_set = {k.lower() for k in site_keys}
        return [cls() for key, cls in SCRAPER_REGISTRY.items() if key in key_set]
    return [cls() for cls in ALL_SCRAPERS]


def search_single(scraper, query, max_results):
    """Search a single site. Returns (scraper_key, site_name, results, error)."""
    try:
        if scraper.browser_only:
            return (scraper.key, scraper.name, [], None)
        results = scraper.search(query, max_results)
        return (scraper.key, scraper.name, results, None)
    except Exception as e:
        logger.warning("Scraper %s failed: %s", scraper.name, e)
        return (scraper.key, scraper.name, [], str(e))


def run_search(query, site_keys=None, max_results=10):
    """Run parallel search across selected sites."""
    scrapers = get_scrapers(site_keys)
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
            key, name, results, error = future.result()
            if error:
                errors[name] = error
            elif results:
                results_by_site[name] = results
            else:
                no_results.append(name)

    elapsed = time.time() - start

    return {
        "results_by_site": results_by_site,
        "errors": errors,
        "no_results": no_results,
        "elapsed": round(elapsed, 1),
        "total_sites": len(scrapers),
    }


@app.route("/")
def index():
    """Search page — show form + results if query provided."""
    query = request.args.get("q", "").strip()
    sites_param = request.args.get("sites", "").strip()
    max_results = request.args.get("max", 10, type=int)

    site_keys = [s.strip() for s in sites_param.split(",") if s.strip()] or None

    # Build list of all sites for the filter checkboxes
    all_sites = [{"key": cls().key, "name": cls().name} for cls in ALL_SCRAPERS]

    if not query:
        return render_template("index.html", all_sites=all_sites)

    data = run_search(query, site_keys=site_keys, max_results=max_results)

    # Flatten results for sorting, preserve site order for grouped view
    all_results = []
    for site_name, results in data["results_by_site"].items():
        for r in results:
            all_results.append(r)

    total_count = len(all_results)

    # Maintain scraper ordering for grouped display
    ordered_site_names = [cls().name for cls in ALL_SCRAPERS]

    return render_template(
        "index.html",
        query=query,
        data=data,
        total_count=total_count,
        ordered_site_names=ordered_site_names,
        all_sites=all_sites,
        selected_sites=site_keys,
        max_results=max_results,
    )


@app.route("/api/search")
def api_search():
    """JSON API endpoint for search."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    sites_param = request.args.get("sites", "").strip()
    max_results = request.args.get("max", 10, type=int)
    site_keys = [s.strip() for s in sites_param.split(",") if s.strip()] or None

    data = run_search(query, site_keys=site_keys, max_results=max_results)

    output = {
        "query": query,
        "results": {},
        "errors": data["errors"],
        "no_results": data["no_results"],
        "elapsed_seconds": data["elapsed"],
    }
    for site_name, results in data["results_by_site"].items():
        output["results"][site_name] = [asdict(r) for r in results]

    return jsonify(output)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
