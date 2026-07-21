"""
core/url_unmasker.py
Regex translation engines stripping affiliate trackers and converting short links
into uniform product links formatted for target agents.
"""

import re
import hashlib
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import requests

from config.settings import (
    AFFILIATE_TOKEN_PATTERNS,
    SHORT_LINK_DOMAINS,
    AGENT_ENDPOINTS,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Compiled Regex Patterns
# ---------------------------------------------------------------------------
# Pre-compile affiliate stripping patterns for performance
_AFFILIATE_COMPILED: List[re.Pattern] = [
    re.compile(pattern, re.IGNORECASE) for pattern in AFFILIATE_TOKEN_PATTERNS
]

# Pattern to detect short link domains
_SHORT_LINK_DOMAIN_PATTERN = re.compile(
    r"^(?:https?://)?([^/]+)(" + "|".join(re.escape(d) for d in SHORT_LINK_DOMAINS) + r")(?:/.*)?$",
    re.IGNORECASE,
)

# Pattern to extract item/product ID from generic URLs
_ITEM_ID_PATTERN = re.compile(
    r"(?:id=|item=|/item/|/product/|/p/|/i/)?(\d{6,})",
    re.IGNORECASE,
)

# Pattern for agent product link detection
_AGENT_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?P<agent>litbuy|allchinabuy|hoobuy|superbuy)\.com"
    r"(?:/[^?\s]*)?(?:\?(?P<query>[^\s]*))?",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# URL Unmasker Result
# ---------------------------------------------------------------------------
class UnmaskedURL:
    """Holds the result of URL unmasking and normalization."""

    __slots__ = (
        "original_url",
        "clean_url",
        "agent_name",
        "agent_product_url",
        "item_id",
        "short_link_domain",
        "tracking_tokens_removed",
        "is_agent_link",
        "confidence",
        "raw_details",
    )

    def __init__(
        self,
        original_url: str = "",
        clean_url: str = "",
        agent_name: str = "",
        agent_product_url: str = "",
        item_id: str = "",
        short_link_domain: str = "",
        tracking_tokens_removed: int = 0,
        is_agent_link: bool = False,
        confidence: float = 0.0,
        raw_details: str = "",
    ):
        self.original_url = original_url
        self.clean_url = clean_url
        self.agent_name = agent_name
        self.agent_product_url = agent_product_url
        self.item_id = item_id
        self.short_link_domain = short_link_domain
        self.tracking_tokens_removed = tracking_tokens_removed
        self.is_agent_link = is_agent_link
        self.confidence = confidence
        self.raw_details = raw_details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_url": self.original_url,
            "clean_url": self.clean_url,
            "agent_name": self.agent_name,
            "agent_product_url": self.agent_product_url,
            "item_id": self.item_id,
            "short_link_domain": self.short_link_domain,
            "tracking_tokens_removed": self.tracking_tokens_removed,
            "is_agent_link": self.is_agent_link,
            "confidence": self.confidence,
            "raw_details": self.raw_details,
        }

    def __repr__(self) -> str:
        return (
            f"<UnmaskedURL agent={self.agent_name!r} item_id={self.item_id!r} "
            f"tokens_removed={self.tracking_tokens_removed}>"
        )


# ---------------------------------------------------------------------------
# URL Normalization Utilities
# ---------------------------------------------------------------------------
def _strip_query_parameters(url: str, params_to_remove: List[str]) -> Tuple[str, int]:
    """
    Remove specific query parameters from a URL.
    Returns the cleaned URL and the count of removed parameters.
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    removed_count = 0

    for param in params_to_remove:
        if param in query_params:
            del query_params[param]
            removed_count += 1

    new_query = urlencode(query_params, doseq=True)
    cleaned = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))
    return cleaned, removed_count


def _remove_affiliate_tokens(url: str) -> Tuple[str, int]:
    """
    Apply all compiled affiliate token patterns to strip tracking parameters.
    Returns cleaned URL and total tokens removed.
    """
    total_removed = 0
    cleaned = url
    for pattern in _AFFILIATE_COMPILED:
        cleaned, n = _strip_query_parameters(cleaned, pattern.findall(cleaned))
        total_removed += n
        # Also remove the raw pattern match if it appears as a fragment or path
        cleaned = pattern.sub("", cleaned)

    # Normalize: remove trailing ?, &, #
    cleaned = re.sub(r"[?&#]+$", "", cleaned)
    return cleaned, total_removed


def _is_short_link(url: str) -> Tuple[bool, Optional[str]]:
    """Detect if the URL is a shortened link and return the short domain if so."""
    match = _SHORT_LINK_DOMAIN_PATTERN.search(url)
    if match:
        return True, match.group(1)
    return False, None


def _resolve_short_link(url: str, timeout: int = REQUEST_TIMEOUT) -> Optional[str]:
    """
    Follow redirects to resolve a short link into its final destination.
    Uses HEAD request first, falls back to GET with stream=False.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    })

    try:
        resp = session.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code >= 400:
            resp = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
        final_url = resp.url
        return final_url
    except requests.RequestException as exc:
        logger.warning("Short link resolution failed for %s: %s", url, exc)
        return None


def _detect_agent(url: str) -> Tuple[str, bool]:
    """
    Detect if a URL belongs to a supported agent and return (agent_name, is_agent_link).
    """
    match = _AGENT_LINK_PATTERN.search(url)
    if match:
        agent = match.group("agent").lower()
        if agent in AGENT_ENDPOINTS:
            return agent, True
    return "", False


def _build_agent_search_url(agent_name: str, item_id: str, keywords: str = "") -> str:
    """
    Build a standardized product search URL for the target agent.
    """
    base = AGENT_ENDPOINTS.get(agent_name, {}).get("search_url", "")
    if not base:
        return ""

    if item_id:
        return f"{base}?id={item_id}"
    elif keywords:
        return f"{base}?q={requests.utils.quote(keywords)}"
    return base


# ---------------------------------------------------------------------------
# Main Unmasker API
# ---------------------------------------------------------------------------
class URLUnmasker:
    """
    Regex translation engine that sweeps community links, strips hidden
    tracking/affiliate tokens, and resolves shortened links into uniform
    product links formatted for target agents.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: Dict[str, UnmaskedURL] = {}
        self._cache_max_size = 500

    def unmask(self, url: str, resolve_short: bool = True) -> UnmaskedURL:
        """
        Unmask a single URL: strip tracking tokens, resolve short links,
        and format for target agents if applicable.
        """
        if not url or not isinstance(url, str):
            return UnmaskedURL(
                original_url=url,
                confidence=0.0,
                raw_details="Invalid or empty URL provided.",
            )

        original_url = url.strip()
        # Cache check
        cache_key = hashlib.sha256(original_url.encode("utf-8")).hexdigest()[:16]
        with self._lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                cached.original_url = original_url
                return cached

        is_short, short_domain = _is_short_link(original_url)
        short_link_domain = short_domain or ""

        current_url = original_url

        # Step 1: Resolve short links
        if is_short and resolve_short:
            resolved = _resolve_short_link(current_url)
            if resolved:
                current_url = resolved
            else:
                current_url = original_url

        # Step 2: Strip affiliate tokens
        cleaned_url, tokens_removed = _remove_affiliate_tokens(current_url)

        # Step 3: Detect agent ownership
        agent_name, is_agent_link = _detect_agent(cleaned_url)

        # Step 4: Extract item ID
        item_id_match = _ITEM_ID_PATTERN.search(cleaned_url)
        item_id = item_id_match.group(1) if item_id_match else ""

        # Step 5: Build formatted agent URL if applicable
        agent_product_url = ""
        if is_agent_link and agent_name:
            keywords = ""
            agent_product_url = _build_agent_search_url(agent_name, item_id, keywords)

        # Confidence scoring
        confidence = 0.5
        if is_agent_link:
            confidence += 0.25
        if item_id:
            confidence += 0.15
        if tokens_removed > 0:
            confidence += 0.10
        confidence = min(confidence, 1.0)

        result = UnmaskedURL(
            original_url=original_url,
            clean_url=cleaned_url,
            agent_name=agent_name,
            agent_product_url=agent_product_url,
            item_id=item_id,
            short_link_domain=short_link_domain,
            tracking_tokens_removed=tokens_removed,
            is_agent_link=is_agent_link,
            confidence=confidence,
            raw_details=f"Resolved from short link: {is_short}; Tokens stripped: {tokens_removed}",
        )

        # Cache management
        with self._lock:
            if len(self._cache) >= self._cache_max_size:
                # Evict oldest 20%
                keys = list(self._cache.keys())
                for old_key in keys[: len(keys) // 5]:
                    del self._cache[old_key]
            self._cache[cache_key] = result

        return result

    def unmask_batch(self, urls: List[str], resolve_short: bool = True) -> List[UnmaskedURL]:
        """
        Unmask a batch of URLs. Returns results in the same order as input.
        """
        results: List[UnmaskedURL] = []
        for url in urls:
            results.append(self.unmask(url, resolve_short=resolve_short))
        return results

    def clear_cache(self) -> None:
        """Clear the internal URL cache."""
        with self._lock:
            self._cache.clear()
