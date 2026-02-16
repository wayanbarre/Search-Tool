from .base import BaseScraper, SearchResult
from .keh import KEHScraper
from .mpb import MPBScraper
from .fredmiranda import FredMirandaScraper
from .usedphotopro import UsedPhotoProScraper
from .reddit import RedditScraper
from .gearfocus import GearFocusScraper
from .adorama import AdoramaScraper
from .bhphoto import BHPhotoScraper
from .lensrentals import LensRentalsScraper

ALL_SCRAPERS = [
    KEHScraper,
    MPBScraper,
    FredMirandaScraper,
    UsedPhotoProScraper,
    RedditScraper,
    GearFocusScraper,
    AdoramaScraper,
    BHPhotoScraper,
    LensRentalsScraper,
]

__all__ = [
    "BaseScraper",
    "SearchResult",
    "ALL_SCRAPERS",
    "KEHScraper",
    "MPBScraper",
    "FredMirandaScraper",
    "UsedPhotoProScraper",
    "RedditScraper",
    "GearFocusScraper",
    "AdoramaScraper",
    "BHPhotoScraper",
    "LensRentalsScraper",
]
