"""
config/settings.py
Global constants, default spreadsheet sources, agent API fallback endpoints,
shipping line rules for offline resilience, and UI theme parameters.
"""

import os
from typing import Dict, List, Any

# ---------------------------------------------------------------------------
# General Application Settings
# ---------------------------------------------------------------------------
APP_NAME = "HaulX"
APP_VERSION = "1.0.0"
APP_BUILD = "Stable"
APP_CODE = "HAULX-STABLE"

# Network / Request timeouts (seconds)
REQUEST_TIMEOUT = 15
SPREADSHEET_REFRESH_INTERVAL = 300  # seconds between automatic re-indexes
IMAGE_SEARCH_TIMEOUT = 20

# ---------------------------------------------------------------------------
# Default Public Spreadsheet Sources
# These are example published CSV export URLs. In a live deployment, the
# user or maintainer would replace these with actual community sheet URLs.
# ---------------------------------------------------------------------------
DEFAULT_SPREADSHEET_SOURCES: List[str] = [
    # Example placeholder URLs — replace with real published CSV links
    "https://docs.google.com/spreadsheets/d/EXAMPLE_SHEET_1/gviz/tq?tqx=out:csv&sheet=Sheet1",
    "https://docs.google.com/spreadsheets/d/EXAMPLE_SHEET_2/gviz/tq?tqx=out:csv&sheet=Products",
]

# Maximum rows to pull per source to keep memory bounded
MAX_ROWS_PER_SOURCE = 5000

# ---------------------------------------------------------------------------
# Agent Base URLs (fallback when live scraping is unavailable)
# ---------------------------------------------------------------------------
AGENT_ENDPOINTS: Dict[str, Dict[str, str]] = {
    "litbuy": {
        "base_url": "https://www.litbuy.com",
        "search_url": "https://www.litbuy.com/search",
        "shipping_info_url": "https://www.litbuy.com/shipping",
        "api_fallback": "https://api.litbuy.com/v1/product/search",
    },
    "allchinabuy": {
        "base_url": "https://www.allchinabuy.com",
        "search_url": "https://www.allchinabuy.com/search",
        "shipping_info_url": "https://www.allchinabuy.com/shipping",
        "api_fallback": "https://api.allchinabuy.com/v1/product/search",
    },
    "hoobuy": {
        "base_url": "https://www.hoobuy.com",
        "search_url": "https://www.hoobuy.com/search",
        "shipping_info_url": "https://www.hoobuy.com/shipping",
        "api_fallback": "https://api.hoobuy.com/v1/product/search",
    },
    "superbuy": {
        "base_url": "https://www.superbuy.com",
        "search_url": "https://www.superbuy.com/search",
        "shipping_info_url": "https://www.superbuy.com/shipping",
        "api_fallback": "https://api.superbuy.com/v1/product/search",
    },
}

# ---------------------------------------------------------------------------
# Shipping Line Fallback Rules (Offline Resilience)
# When live web endpoints fail, these structured dictionaries provide
# fallback base fees, per-kg rates, and volumetric divisor rules.
# ---------------------------------------------------------------------------
SHIPPING_LINE_RULES: Dict[str, Dict[str, Any]] = {
    "US": {
        "carriers": {
            "Tax-Free Line": {
                "base_fee": 18.00,
                "per_kg": 5.80,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.0,
                "remote_area_fee": 0.00,
                "notes": "Standard economy line, 12-18 days.",
            },
            "E-EMS": {
                "base_fee": 22.00,
                "per_kg": 7.50,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.0,
                "remote_area_fee": 0.00,
                "notes": "Express tracking, 7-12 days.",
            },
            "DHL-Tier1": {
                "base_fee": 35.00,
                "per_kg": 12.00,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.075,
                "remote_area_fee": 15.00,
                "notes": "Fastest option, 3-5 days.",
            },
            "DHL-Tier2": {
                "base_fee": 42.00,
                "per_kg": 14.50,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.085,
                "remote_area_fee": 20.00,
                "notes": "Premium tier for heavier packages.",
            },
        }
    },
    "EU": {
        "carriers": {
            "Tax-Free Line": {
                "base_fee": 20.00,
                "per_kg": 6.20,
                "volumetric_divisor": 6000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.0,
                "remote_area_fee": 0.00,
                "notes": "Standard economy, 15-22 days.",
            },
            "E-EMS": {
                "base_fee": 25.00,
                "per_kg": 8.00,
                "volumetric_divisor": 6000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.0,
                "remote_area_fee": 0.00,
                "notes": "Express tracking, 8-14 days.",
            },
            "DHL-Tier1": {
                "base_fee": 38.00,
                "per_kg": 13.00,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.08,
                "remote_area_fee": 18.00,
                "notes": "Fastest option, 4-6 days.",
            },
            "DHL-Tier2": {
                "base_fee": 45.00,
                "per_kg": 15.50,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.09,
                "remote_area_fee": 25.00,
                "notes": "Premium tier for heavier packages.",
            },
        }
    },
    "UK": {
        "carriers": {
            "Tax-Free Line": {
                "base_fee": 19.00,
                "per_kg": 5.90,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.0,
                "remote_area_fee": 0.00,
                "notes": "Standard economy, 12-18 days.",
            },
            "E-EMS": {
                "base_fee": 23.00,
                "per_kg": 7.80,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.0,
                "remote_area_fee": 0.00,
                "notes": "Express tracking, 7-12 days.",
            },
            "DHL-Tier1": {
                "base_fee": 36.00,
                "per_kg": 12.50,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.075,
                "remote_area_fee": 16.00,
                "notes": "Fastest option, 3-5 days.",
            },
            "DHL-Tier2": {
                "base_fee": 43.00,
                "per_kg": 15.00,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.085,
                "remote_area_fee": 22.00,
                "notes": "Premium tier for heavier packages.",
            },
        }
    },
    "CA": {
        "carriers": {
            "Tax-Free Line": {
                "base_fee": 21.00,
                "per_kg": 6.50,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.0,
                "remote_area_fee": 0.00,
                "notes": "Standard economy, 14-20 days.",
            },
            "E-EMS": {
                "base_fee": 26.00,
                "per_kg": 8.50,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.0,
                "remote_area_fee": 0.00,
                "notes": "Express tracking, 8-14 days.",
            },
            "DHL-Tier1": {
                "base_fee": 40.00,
                "per_kg": 13.50,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.08,
                "remote_area_fee": 20.00,
                "notes": "Fastest option, 4-6 days.",
            },
            "DHL-Tier2": {
                "base_fee": 48.00,
                "per_kg": 16.00,
                "volumetric_divisor": 5000,
                "first_weight_kg": 0.5,
                "additional_weight_kg": 0.5,
                "fuel_surcharge_pct": 0.09,
                "remote_area_fee": 28.00,
                "notes": "Premium tier for heavier packages.",
            },
        }
    },
}

# ---------------------------------------------------------------------------
# Agent-Specific Markup and Fee Structures
# Each agent applies different service fees, handling fees, and promotional
# line discounts on top of the base shipping cost.
# ---------------------------------------------------------------------------
AGENT_MARKUP_RULES: Dict[str, Dict[str, Any]] = {
    "litbuy": {
        "service_fee_pct": 0.015,       # 1.5% service fee on item price
        "handling_fee": 3.00,           # flat per parcel
        "insurance_pct": 0.008,         # 0.8% optional insurance (included in calc by default)
        "promo_discount_pct": 0.0,      # user-configurable promotional discount
        "currency": "CNY",
        "supports_tax_free": True,
        "tax_free_line_name": "Tax-Free Line",
    },
    "allchinabuy": {
        "service_fee_pct": 0.012,       # 1.2%
        "handling_fee": 2.50,
        "insurance_pct": 0.006,
        "promo_discount_pct": 0.0,
        "currency": "CNY",
        "supports_tax_free": True,
        "tax_free_line_name": "Tax-Free Line",
    },
    "hoobuy": {
        "service_fee_pct": 0.010,       # 1.0%
        "handling_fee": 2.00,
        "insurance_pct": 0.005,
        "promo_discount_pct": 0.0,
        "currency": "CNY",
        "supports_tax_free": True,
        "tax_free_line_name": "Tax-Free Line",
    },
    "superbuy": {
        "service_fee_pct": 0.018,       # 1.8%
        "handling_fee": 4.00,
        "insurance_pct": 0.010,
        "promo_discount_pct": 0.0,
        "currency": "CNY",
        "supports_tax_free": True,
        "tax_free_line_name": "Tax-Free Line",
    },
}

# ---------------------------------------------------------------------------
# URL Unmasker Regex Patterns
# ---------------------------------------------------------------------------
AFFILIATE_TOKEN_PATTERNS: List[str] = [
    r"[?&](?:utm_source|utm_medium|utm_campaign|utm_term|utm_content|gclid|fbclid|msclkid|ref|source|affiliate|aff_id|aff_sub|aff_sub2|click_id|session_id|tracking_id)=[^&#]*",
    r"[?&](?:spm|pid|id|item_id|product_id)=\d+\.\d+",
    r"https?://(?:s\.click\.aliexpress\.com|ad\.doubleclick\.net|go\.skimresources\.com|aff\.example\.com)/[^\s]*",
]

SHORT_LINK_DOMAINS: List[str] = [
    "bit.ly",
    "suo.yt",
    "t.cn",
    "dwz.cn",
    "tinyurl.com",
    "ow.ly",
    "t.co",
]

# ---------------------------------------------------------------------------
# UI Theme Defaults
# ---------------------------------------------------------------------------
UI_THEME: Dict[str, Any] = {
    "mode": "Dark",          # "System", "Dark", "Light"
    "primary_color": "#1f6aa5",
    "secondary_color": "#144870",
    "text_color": "#ffffff",
    "text_color_secondary": "#aaaaaa",
    "font_family": "Segoe UI" if os.name == "nt" else "Helvetica",
    "font_size_small": 11,
    "font_size_normal": 13,
    "font_size_large": 16,
    "font_size_title": 20,
    "window_width": 1280,
    "window_height": 800,
    "sidebar_width": 220,
    "status_bar_height": 30,
}

# ---------------------------------------------------------------------------
# Image Search Engine Defaults
# ---------------------------------------------------------------------------
IMAGE_SEARCH_ENGINES: List[Dict[str, str]] = [
    {
        "name": "Google Lens",
        "endpoint": "https://lens.google.com/uploadbyurl",
        "method": "POST",
        "content_type": "multipart/form-data",
    },
    {
        "name": "Bing Visual Search",
        "endpoint": "https://www.bing.com/images/searchbyimage",
        "method": "POST",
        "content_type": "multipart/form-data",
    },
    {
        "name": "Yandex Image Search",
        "endpoint": "https://yandex.com/images/search",
        "method": "POST",
        "content_type": "multipart/form-data",
    },
]

# ---------------------------------------------------------------------------
# Spreadsheet Column Mapping Heuristics
# ---------------------------------------------------------------------------
SPREADSHEET_COLUMN_MAPPING: Dict[str, List[str]] = {
    "category": ["category", "type", "class", "品类", "分类"],
    "brand": ["brand", "brandname", "品牌", "牌子"],
    "price_cny": ["price", "cny", "rmb", "price_cny", "价格", "售价"],
    "qc_image": ["qc", "qc_img", "qc_image", "图片", "实拍", "实物图"],
    "product_link": ["link", "url", "product_link", "链接", "购买链接"],
    "description": ["description", "desc", "备注", "描述", "说明"],
}

# ---------------------------------------------------------------------------
# Supported Destinations
# ---------------------------------------------------------------------------
SUPPORTED_DESTINATIONS: List[str] = ["US", "EU", "UK", "CA"]

# ---------------------------------------------------------------------------
# Supported Agents
# ---------------------------------------------------------------------------
SUPPORTED_AGENTS: List[str] = ["litbuy", "allchinabuy", "hoobuy", "superbuy"]
