"""
core/image_search_engine.py
Dedicated network engine that streams local image uploads or URL references,
processes them to simulate reverse visual lookups on web endpoints, parses
structural item results (Taobao, Weidian, 1688), and outputs raw product identifiers.
"""

import io
import re
import os
import hashlib
import base64
import threading
import queue
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import requests
from PIL import Image

from config.settings import (
    REQUEST_TIMEOUT,
    IMAGE_SEARCH_TIMEOUT,
    IMAGE_SEARCH_ENGINES,
    AGENT_ENDPOINTS,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result Data Structures
# ---------------------------------------------------------------------------
class VisualSearchResult:
    """Represents a single parsed visual search result."""

    __slots__ = (
        "engine_name",
        "source_url",
        "title",
        "item_id",
        "platform",
        "price_cny",
        "image_url",
        "product_link",
        "confidence",
        "raw_snippet",
    )

    def __init__(
        self,
        engine_name: str = "",
        source_url: str = "",
        title: str = "",
        item_id: str = "",
        platform: str = "",
        price_cny: Optional[float] = None,
        image_url: str = "",
        product_link: str = "",
        confidence: float = 0.0,
        raw_snippet: str = "",
    ):
        self.engine_name = engine_name
        self.source_url = source_url
        self.title = title
        self.item_id = item_id
        self.platform = platform
        self.price_cny = price_cny
        self.image_url = image_url
        self.product_link = product_link
        self.confidence = confidence
        self.raw_snippet = raw_snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_name": self.engine_name,
            "source_url": self.source_url,
            "title": self.title,
            "item_id": self.item_id,
            "platform": self.platform,
            "price_cny": self.price_cny,
            "image_url": self.image_url,
            "product_link": self.product_link,
            "confidence": self.confidence,
            "raw_snippet": self.raw_snippet,
        }

    def __repr__(self) -> str:
        return (
            f"<VisualSearchResult platform={self.platform!r} item_id={self.item_id!r} "
            f"title={self.title!r} confidence={self.confidence:.2f}>"
        )


# ---------------------------------------------------------------------------
# Image Preprocessing
# ---------------------------------------------------------------------------
def _load_image_from_bytes(data: bytes) -> Optional[Image.Image]:
    """Load a PIL Image from raw bytes."""
    try:
        return Image.open(io.BytesIO(data))
    except Exception as exc:
        logger.error("Failed to load image from bytes: %s", exc)
        return None


def _load_image_from_path(path: str) -> Optional[Image.Image]:
    """Load a PIL Image from a filesystem path."""
    try:
        return Image.open(path)
    except Exception as exc:
        logger.error("Failed to load image from path %s: %s", path, exc)
        return None


def _resize_for_upload(image: Image.Image, max_dim: int = 1024) -> bytes:
    """
    Resize image so the longest dimension does not exceed max_dim,
    then return as JPEG bytes.
    """
    image = image.convert("RGB")
    w, h = image.size
    if max(w, h) > max_dim:
        ratio = max_dim / float(max(w, h))
        new_size = (int(w * ratio), int(h * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _encode_image_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


# ---------------------------------------------------------------------------
# Endpoint Simulation & Parsing
# ---------------------------------------------------------------------------
def _build_multipart_payload(image_bytes: bytes, filename: str = "query.jpg") -> Tuple[bytes, str]:
    """Build a multipart/form-data payload for image upload."""
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + image_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def _extract_platform_from_url(url: str) -> str:
    """Heuristic platform detection from URL hostname."""
    hostname = urlparse(url).hostname or ""
    host_lower = hostname.lower()
    if "taobao" in host_lower:
        return "taobao"
    if "weidian" in host_lower:
        return "weidian"
    if "1688" in host_lower:
        return "1688"
    if "tmall" in host_lower:
        return "tmall"
    if "aliexpress" in host_lower:
        return "aliexpress"
    return "unknown"


def _parse_structural_item_id(url: str) -> str:
    """Extract numeric item ID from Taobao/Weidian/1688 style URLs."""
    patterns = [
        r"(\d{9,})",           # Generic long numeric ID
        r"id=(\d+)",           # Query param id=
        r"/(\d+)\.html",       # Path segment /123456789.html
        r"item/(\d+)",         # Path segment /item/123456789
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def _parse_result_title_and_price(html_snippet: str) -> Tuple[str, Optional[float]]:
    """
    Attempt to extract a title and price from an HTML snippet using regex.
    This is a structural parser that handles common markup patterns.
    """
    title = ""
    price = None

    # Title extraction: <title> tags or heading tags
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_snippet, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
    if not title:
        h_match = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html_snippet, re.IGNORECASE | re.DOTALL)
        if h_match:
            title = re.sub(r"<[^>]+>", "", h_match.group(1)).strip()

    # Price extraction: look for currency patterns
    price_match = re.search(
        r"[\$€£¥]?\s*(\d{1,4}(?:\.\d{1,2})?)",
        html_snippet,
        re.IGNORECASE,
    )
    if price_match:
        try:
            price = float(price_match.group(1))
        except ValueError:
            price = None

    return title, price


# ---------------------------------------------------------------------------
# Engine Worker
# ---------------------------------------------------------------------------
class ImageSearchEngine:
    """
    Dedicated network engine for reverse image search.
    Supports local image uploads and URL references.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._result_queue: "queue.Queue[VisualSearchResult]" = queue.Queue()

    def search_from_file(
        self,
        file_path: str,
        engines: Optional[List[str]] = None,
        timeout: int = IMAGE_SEARCH_TIMEOUT,
    ) -> List[VisualSearchResult]:
        """Upload a local image file and search across specified engines."""
        if not os.path.isfile(file_path):
            logger.error("Image file not found: %s", file_path)
            return []

        image = _load_image_from_path(file_path)
        if image is None:
            return []

        return self._search_image(image, engines=engines, timeout=timeout)

    def search_from_url(
        self,
        image_url: str,
        engines: Optional[List[str]] = None,
        timeout: int = IMAGE_SEARCH_TIMEOUT,
    ) -> List[VisualSearchResult]:
        """Download an image from a URL and search across specified engines."""
        try:
            resp = self._session.get(image_url, timeout=timeout)
            resp.raise_for_status()
            image = _load_image_from_bytes(resp.content)
            if image is None:
                return []
        except requests.RequestException as exc:
            logger.error("Failed to download image from %s: %s", image_url, exc)
            return []

        return self._search_image(image, engines=engines, timeout=timeout)

    def search_from_bytes(
        self,
        image_bytes: bytes,
        engines: Optional[List[str]] = None,
        timeout: int = IMAGE_SEARCH_TIMEOUT,
    ) -> List[VisualSearchResult]:
        """Search using raw image bytes."""
        image = _load_image_from_bytes(image_bytes)
        if image is None:
            return []
        return self._search_image(image, engines=engines, timeout=timeout)

    def _search_image(
        self,
        image: Image.Image,
        engines: Optional[List[str]] = None,
        timeout: int = IMAGE_SEARCH_TIMEOUT,
    ) -> List[VisualSearchResult]:
        """Internal: process image and query configured search engines."""
        if engines is None:
            engines = [eng["name"] for eng in IMAGE_SEARCH_ENGINES]

        image_bytes = _resize_for_upload(image)
        image_b64 = _encode_image_base64(image_bytes)

        results: List[VisualSearchResult] = []
        threads: List[threading.Thread] = []

        def _engine_worker(engine_name: str):
            try:
                engine_config = next(
                    (e for e in IMAGE_SEARCH_ENGINES if e["name"] == engine_name),
                    None,
                )
                if not engine_config:
                    logger.warning("Unknown engine requested: %s", engine_name)
                    return

                endpoint = engine_config["endpoint"]
                method = engine_config["method"]

                payload, content_type = _build_multipart_payload(image_bytes)

                headers = {
                    "Content-Type": content_type,
                }

                if method.upper() == "POST":
                    resp = self._session.post(
                        endpoint,
                        data=payload,
                        headers=headers,
                        timeout=timeout,
                        allow_redirects=True,
                    )
                else:
                    # Some engines expect a GET with the base64 image in query
                    params = {"image": image_b64}
                    resp = self._session.get(
                        endpoint,
                        params=params,
                        headers=headers,
                        timeout=timeout,
                        allow_redirects=True,
                    )

                resp.raise_for_status()
                html_text = resp.text

                # Parse structural results from the returned HTML
                parsed = self._parse_engine_response(engine_name, html_text)
                for pr in parsed:
                    self._result_queue.put(pr)
                    results.append(pr)

            except requests.RequestException as exc:
                logger.warning("Engine %s request failed: %s", engine_name, exc)
            except Exception as exc:
                logger.error("Engine %s unexpected error: %s", engine_name, exc)

        for engine_name in engines:
            t = threading.Thread(target=_engine_worker, args=(engine_name,), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=timeout + 5)

        return results

    def _parse_engine_response(
        self, engine_name: str, html_text: str
    ) -> List[VisualSearchResult]:
        """
        Parse HTML response from a visual search engine and extract structured
        product identifiers. Handles common Taobao/Weidian/1688 result patterns.
        """
        results: List[VisualSearchResult] = []

        # Extract all href attributes that point to known platforms
        link_pattern = re.compile(
            r'href=["\'](.*?(?:taobao|weidian|1688|tmall|aliexpress).*?)["\']',
            re.IGNORECASE,
        )
        found_links = link_pattern.findall(html_text)

        # Extract image src patterns for QC/reference images
        img_pattern = re.compile(
            r'src=["\'](https?://[^"\']+\.(?:jpg|jpeg|png|webp))["\']',
            re.IGNORECASE,
        )
        found_images = img_pattern.findall(html_text)

        seen_links = set()
        for idx, link in enumerate(found_links):
            if link in seen_links:
                continue
            seen_links.add(link)

            platform = _extract_platform_from_url(link)
            item_id = _parse_structural_item_id(link)
            title, price = _parse_result_title_and_price(html_text)

            img_url = found_images[idx] if idx < len(found_images) else ""

            confidence = 0.85
            if item_id:
                confidence += 0.10
            if platform != "unknown":
                confidence += 0.05
            confidence = min(confidence, 1.0)

            results.append(
                VisualSearchResult(
                    engine_name=engine_name,
                    source_url=link,
                    title=title,
                    item_id=item_id,
                    platform=platform,
                    price_cny=price,
                    image_url=img_url,
                    product_link=link,
                    confidence=confidence,
                    raw_snippet=html_text[:500],
                )
            )

        # If no structured links were found, return a generic result
        if not results:
            results.append(
                VisualSearchResult(
                    engine_name=engine_name,
                    source_url="",
                    title="No structured result extracted",
                    item_id="",
                    platform="unknown",
                    price_cny=None,
                    image_url="",
                    product_link="",
                    confidence=0.0,
                    raw_snippet=html_text[:500],
                )
            )

        return results

    def stop(self) -> None:
        """Signal any running workers to stop."""
        self._stop_event.set()

    def drain_results(self, max_items: int = 50) -> List[VisualSearchResult]:
        """Drain queued results."""
        items: List[VisualSearchResult] = []
        for _ in range(max_items):
            try:
                items.append(self._result_queue.get_nowait())
            except queue.Empty:
                break
        return items
