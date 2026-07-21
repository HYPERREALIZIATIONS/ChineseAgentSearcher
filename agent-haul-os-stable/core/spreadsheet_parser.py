"""
core/spreadsheet_parser.py
Asynchronous public Google Sheets stream processing & keyword indexing engine.
Uses threading.Thread and requests to pull public CSV streams into an optimized
in-memory search index, binding Category, Brand, Price in CNY, and QC images.
"""

import re
import csv
import io
import threading
import queue
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import pandas as pd

from config.settings import (
    DEFAULT_SPREADSHEET_SOURCES,
    MAX_ROWS_PER_SOURCE,
    REQUEST_TIMEOUT,
    SPREADSHEET_COLUMN_MAPPING,
    SUPPORTED_DESTINATIONS,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------
class ProductEntry:
    """Represents a single indexed product row from a spreadsheet source."""

    __slots__ = (
        "source_url",
        "row_index",
        "category",
        "brand",
        "price_cny",
        "qc_image_url",
        "product_link",
        "description",
        "raw_data",
    )

    def __init__(
        self,
        source_url: str,
        row_index: int,
        category: str = "",
        brand: str = "",
        price_cny: Optional[float] = None,
        qc_image_url: str = "",
        product_link: str = "",
        description: str = "",
        raw_data: Optional[Dict[str, Any]] = None,
    ):
        self.source_url = source_url
        self.row_index = row_index
        self.category = category
        self.brand = brand
        self.price_cny = price_cny
        self.qc_image_url = qc_image_url
        self.product_link = product_link
        self.description = description
        self.raw_data = raw_data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_url": self.source_url,
            "row_index": self.row_index,
            "category": self.category,
            "brand": self.brand,
            "price_cny": self.price_cny,
            "qc_image_url": self.qc_image_url,
            "product_link": self.product_link,
            "description": self.description,
        }

    def __repr__(self) -> str:
        return (
            f"<ProductEntry idx={self.row_index} cat={self.category!r} "
            f"brand={self.brand!r} price={self.price_cny} link={self.product_link!r}>"
        )


class SearchIndex:
    """In-memory inverted search index for fast keyword lookups."""

    def __init__(self):
        self._lock = threading.RLock()
        self._entries: List[ProductEntry] = []
        self._inverted_index: Dict[str, List[int]] = {}
        self._token_pattern = re.compile(r"\w+", re.IGNORECASE)

    def add_entry(self, entry: ProductEntry) -> None:
        """Add a product entry to the index."""
        with self._lock:
            idx = len(self._entries)
            self._entries.append(entry)
            tokens = self._tokenize(entry)
            for token in tokens:
                if token not in self._inverted_index:
                    self._inverted_index[token] = []
                self._inverted_index[token].append(idx)

    def add_entries(self, entries: List[ProductEntry]) -> None:
        """Bulk-add entries."""
        for entry in entries:
            self.add_entry(entry)

    def _tokenize(self, entry: ProductEntry) -> List[str]:
        """Extract searchable tokens from a product entry."""
        text_parts = [
            entry.category or "",
            entry.brand or "",
            entry.description or "",
            entry.product_link or "",
        ]
        text = " ".join(text_parts).lower()
        tokens = self._token_pattern.findall(text)
        return list(set(tokens))

    def search(self, query: str, max_results: int = 100) -> List[ProductEntry]:
        """Return up to max_results entries matching the query tokens."""
        query = query.strip().lower()
        if not query:
            return []

        query_tokens = list(set(self._token_pattern.findall(query)))
        if not query_tokens:
            return []

        with self._lock:
            score_map: Dict[int, int] = {}
            for token in query_tokens:
                for idx in self._inverted_index.get(token, []):
                    score_map[idx] = score_map.get(idx, 0) + 1

            # Sort by relevance score descending, then by row index ascending
            sorted_indices = sorted(
                score_map.keys(),
                key=lambda idx: (-score_map[idx], idx),
            )

            results = []
            for idx in sorted_indices[:max_results]:
                results.append(self._entries[idx])
            return results

    def size(self) -> int:
        with self._lock:
            return len(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._inverted_index.clear()


# ---------------------------------------------------------------------------
# Column Normalization
# ---------------------------------------------------------------------------
def _normalize_column_name(name: str) -> str:
    """Map raw column header to canonical field name."""
    name_clean = name.strip().lower().replace(" ", "_").replace("-", "_")
    for canonical, aliases in SPREADSHEET_COLUMN_MAPPING.items():
        if name_clean in [a.lower().replace(" ", "_") for a in aliases]:
            return canonical
    return name_clean


def _parse_price(value: Any) -> Optional[float]:
    """Attempt to convert a price cell value to float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "-", "n/a"):
        return None
    # Remove currency symbols and commas
    s = re.sub(r"[^\d\.\-]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


def _normalize_entry(
    source_url: str, row_index: int, row: Dict[str, Any]
) -> ProductEntry:
    """Convert a raw spreadsheet row dict into a ProductEntry."""
    category = str(row.get("category", "") or "").strip()
    brand = str(row.get("brand", "") or "").strip()
    price_cny = _parse_price(row.get("price_cny"))
    qc_image_url = str(row.get("qc_image", "") or "").strip()
    product_link = str(row.get("product_link", "") or "").strip()
    description = str(row.get("description", "") or "").strip()

    return ProductEntry(
        source_url=source_url,
        row_index=row_index,
        category=category,
        brand=brand,
        price_cny=price_cny,
        qc_image_url=qc_image_url,
        product_link=product_link,
        description=description,
        raw_data=row,
    )


# ---------------------------------------------------------------------------
# CSV Fetcher Workers
# ---------------------------------------------------------------------------
def _fetch_csv_stream(url: str, timeout: int = REQUEST_TIMEOUT) -> Optional[str]:
    """Download a CSV from a URL and return its text content, or None on failure."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/csv,application/octet-stream,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logger.warning("Failed to fetch CSV from %s: %s", url, exc)
        return None


def _parse_csv_text(
    csv_text: str, source_url: str, max_rows: int = MAX_ROWS_PER_SOURCE
) -> List[ProductEntry]:
    """Parse raw CSV text into a list of ProductEntry objects."""
    entries: List[ProductEntry] = []
    try:
        # Use pandas for robust CSV parsing
        df = pd.read_csv(
            io.StringIO(csv_text),
            dtype=str,
            keep_default_na=False,
            na_values=["", "NaN", "nan", "None", "none"],
            nrows=max_rows,
        )
        # Normalize column names
        df.columns = [_normalize_column_name(col) for col in df.columns]

        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            entry = _normalize_entry(source_url, int(idx), row_dict)
            entries.append(entry)
    except Exception as exc:
        logger.error("CSV parsing failed for %s: %s", source_url, exc)
        # Fallback: manual CSV parsing
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            for idx, row in enumerate(reader):
                if idx >= max_rows:
                    break
                normalized_row = {
                    _normalize_column_name(k): v for k, v in row.items()
                }
                entry = _normalize_entry(source_url, idx, normalized_row)
                entries.append(entry)
        except Exception as fallback_exc:
            logger.error("Fallback CSV parsing also failed: %s", fallback_exc)

    return entries


# ---------------------------------------------------------------------------
# Public Spreadsheet Parser API
# ---------------------------------------------------------------------------
class SpreadsheetParser:
    """
    Threaded asynchronous public Google Sheets stream processing engine.
    Pulls public CSV exports into an in-memory search index.
    """

    def __init__(self, sources: Optional[List[str]] = None):
        self.sources = sources if sources is not None else list(DEFAULT_SPREADSHEET_SOURCES)
        self.index = SearchIndex()
        self._status: Dict[str, str] = {}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._progress_queue: "queue.Queue[str]" = queue.Queue()

    def get_status(self) -> Dict[str, str]:
        with self._lock:
            return dict(self._status)

    def get_indexed_count(self) -> int:
        return self.index.size()

    def start_async_indexing(self) -> None:
        """Launch a background thread to fetch and index all spreadsheet sources."""
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning("Indexing thread already running.")
            return

        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._indexing_worker,
            name="SpreadsheetIndexer",
            daemon=True,
        )
        self._worker_thread.start()
        logger.info("Started async spreadsheet indexing for %d sources.", len(self.sources))

    def stop_async_indexing(self) -> None:
        """Signal the indexing thread to stop."""
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5.0)

    def _indexing_worker(self) -> None:
        """Worker thread body: iterates sources and feeds data into the index."""
        total_sources = len(self.sources)
        completed = 0
        errors = 0

        with ThreadPoolExecutor(max_workers=min(4, total_sources)) as executor:
            future_to_url = {
                executor.submit(_fetch_csv_stream, url): url for url in self.sources
            }

            for future in as_completed(future_to_url):
                if self._stop_event.is_set():
                    break

                url = future_to_url[future]
                with self._lock:
                    self._status[url] = "fetching"

                try:
                    csv_text = future.result()
                    if csv_text:
                        with self._lock:
                            self._status[url] = "parsing"
                        entries = _parse_csv_text(csv_text, url)
                        if entries:
                            self.index.add_entries(entries)
                            with self._lock:
                                self._status[url] = f"indexed ({len(entries)} rows)"
                            self._progress_queue.put(
                                f"Indexed {len(entries)} rows from {url}"
                            )
                        else:
                            with self._lock:
                                self._status[url] = "empty"
                            self._progress_queue.put(f"No data rows found in {url}")
                    else:
                        with self._lock:
                            self._status[url] = "fetch_failed"
                        self._progress_queue.put(f"Fetch failed for {url}")
                        errors += 1
                except Exception as exc:
                    with self._lock:
                        self._status[url] = f"error: {exc}"
                    self._progress_queue.put(f"Error indexing {url}: {exc}")
                    errors += 1

                completed += 1
                self._progress_queue.put(
                    f"Progress: {completed}/{total_sources} sources processed."
                )

        with self._lock:
            self._status["_meta"] = (
                f"completed: {completed}, errors: {errors}, "
                f"total_indexed: {self.index.size()}"
            )
        self._progress_queue.put("Indexing complete.")

    def search(self, query: str, max_results: int = 100) -> List[ProductEntry]:
        """Perform a search across the indexed spreadsheets."""
        return self.index.search(query, max_results=max_results)

    def clear_index(self) -> None:
        """Reset the index and status."""
        with self._lock:
            self.index.clear()
            self._status.clear()

    def refresh(self) -> None:
        """Stop any running indexer, clear, and restart."""
        self.stop_async_indexing()
        self.clear_index()
        self.start_async_indexing()
