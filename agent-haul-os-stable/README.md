# Agent Haul OS — Stable Modular Desktop Application

---

## ⚠️ CRITICAL INSTABILITY WARNING — PERMANENT NOTICE ⚠️

**THIS SOFTWARE RELIES ENTIRELY ON LIVE, EXTERNAL, THIRD-PARTY WEB STRUCTURES THAT MAY CHANGE OR BREAK WITHOUT NOTICE.**

- Google Lens endpoints, Taobao/Weidian/1688 HTML layouts, agent logistics documentation pages, and community Google Sheets structures are **not under our control**.
- When upstream platforms update their markup, data schemas, or anti-bot measures, **functions in this application will break silently or with errors until patched**.
- The developers and contributors of this project provide **no guarantee of uptime, accuracy, or compatibility** with future external platform changes.
- **By using this software, you acknowledge that reverse-engineering and scraping of public web resources may violate the Terms of Service of certain platforms. You are solely responsible for ensuring your use complies with applicable laws and platform policies.**
- This project is released for **educational and research purposes only**.

**If any feature stops working, check the project repository for patched releases or submit an issue with the broken endpoint details.**

---

## Core Problems Solved

### 1. Spreadsheet Fragmentation
The shopping-agent community distributes product catalogs across hundreds of unorganized, slow, and often deprecated Google Sheets. Finding a specific fashion item (e.g., "BAPE shark hoodie size L green") requires manually opening dozens of spreadsheets, scrolling through thousands of rows, and cross-referencing prices and QC images.

**Agent Haul OS** aggregates public community spreadsheets into a unified, in-memory search index. Users type a keyword once and instantly receive categorized, brand-tagged results with CNY pricing and QC photo references — no more tab-switching marathons.

### 2. Freight Blindness
Before submitting a haul, buyers must compare:
- Item price in CNY across multiple agents (LitBuy, AllChinaBuy, Hoobuy, Superbuy).
- International shipping cost, which depends on **actual weight** vs **volumetric weight** (`(L × W × H) / 5000` or `/ 6000` depending on destination and carrier).
- Additional fees (handling, insurance, remote-area surcharges).
- Agent-specific markup structures and promotional line availability.

Freight costs can sometimes **exceed the item price itself**, making blind purchases financially dangerous. Yet no unified tool exists to compute these values side-by-side in real time.

**Agent Haul OS** includes a live freight matrix that accepts package dimensions, destination country, and agent markup rules, then instantly calculates and compares total landed cost across all four major agents.

---

## Project Architecture

```
agent-haul-os-stable/
├── README.md                  # This document
├── requirements.txt           # Python dependencies
├── setup.py                   # Package configuration
├── compile_portable.py        # PyInstaller portable compilation automation
├── main_desktop.py            # Application entry point & thread orchestrator
├── config/
│   ├── __init__.py
│   └── settings.py            # Global constants, fallback shipping rules, agent endpoints
├── core/
│   ├── __init__.py
│   ├── spreadsheet_parser.py  # Async CSV stream processing & keyword indexing
│   ├── image_search_engine.py # Reverse image search simulation worker
│   ├── shipping_calculator.py # Actual vs volumetric weight math engine
│   └── url_unmasker.py        # Affiliate token stripping & short-link resolution
└── ui/
    ├── __init__.py
    ├── layout.py              # CustomTkinter base window, dark theme, status bars
    ├── search_panel.py        # Text search & image upload trigger panel
    └── freight_matrix.py      # Multi-agent comparative data grid
```

---

## Installation (Native Python)

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Internet connection for initial dependency download and web scraping functionality

### Step-by-Step

1. **Clone or download** this repository to your local machine.
2. **Open a terminal** and navigate into the project root folder:
   ```bash
   cd agent-haul-os-stable
   ```
3. **Install dependencies** using pip:
   ```bash
   pip install -r requirements.txt
   ```
4. **Launch the application** natively:
   ```bash
   python main_desktop.py
   ```
5. The GUI window should appear. Use the search panel to query spreadsheets, upload images for visual search, and compute freight via the matrix panel.

---

## Portable Compilation (PyInstaller)

To compile the entire modular project into a single portable executable (`.exe` on Windows, `.app` on macOS, or binary on Linux):

1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the automation script:
   ```bash
   python compile_portable.py
   ```
3. The script invokes PyInstaller with `--onedir` or `--onefile` mode, bundles all core/ui/config modules, and binds any asset directories via `--add-data`.
4. The resulting portable build will be placed in the `dist/` directory.

**Platform Notes:**
- **Windows:** Run `compile_portable.py` from a Command Prompt or PowerShell with Administrator privileges if your Python installation is system-wide. Output will be `dist/AgentHaulOS.exe`.
- **macOS:** Run from Terminal. You may need to allow the binary in **System Settings → Privacy & Security** after first launch. Output will be `dist/AgentHaulOS.app`.
- **Linux:** Run from shell. Output will be `dist/AgentHaulOS`.

---

## Usage Overview

### Spreadsheet Parser
- The parser pulls public CSV streams from pre-configured community Google Sheets URLs.
- It indexes columns: Category, Brand, Price (CNY), QC Image URL, and Product Link.
- Search is case-insensitive and supports partial keyword matching across all indexed fields.

### Image Search Engine (Google Photo Mode)
- Click the image upload button to select a local file.
- The engine simulates a reverse visual lookup against public web endpoints.
- Parsed results return structural item identifiers (Taobao ID, Weidian shop link, 1688 product code).

### Freight Matrix
- Enter package dimensions: Length, Width, Height (in centimeters).
- Enter actual package weight (in kilograms).
- Select destination country: US, EU, UK, CA.
- The calculator computes:
  - **Actual Weight** vs **Volumetric Weight** — whichever is greater is the chargeable weight.
  - Per-agent base fees, per-kg rates, and handling fees.
  - **Total Landed Cost** = Item Price + Shipping + Fees.
- Results update in real time as you adjust sliders or change destination.

### URL Unmasker
- Paste any affiliate-tracked or shortened community link.
- The engine strips hidden tracking tokens using compiled regex patterns.
- Resolves short links (e.g., `bit.ly`, `suo.yt`, `s.click.aliexpress.com`) into canonical product URLs formatted for your chosen agent.

---

## Known Limitations & Troubleshooting

| Issue | Cause | Mitigation |
|-------|-------|------------|
| Spreadsheet search returns no results | Google Sheets published CSV URL changed or sheet was deleted | Update the source URL in `config/settings.py` under `DEFAULT_SPREADSHEET_SOURCES` |
| Image search returns empty | Public visual-search endpoint structure changed | Check `core/image_search_engine.py` for endpoint URL updates; report broken endpoint |
| Freight costs look incorrect | Agent logistics HTML or API structure changed | Verify line rules in `config/settings.py` against the agent's official shipping documentation |
| GUI freezes during search | Network timeout on remote CSV stream | Increase `REQUEST_TIMEOUT` in `config/settings.py`; ensure stable internet connection |
| PyInstaller build fails | Missing hidden imports for `customtkinter` or `PIL` | Add the missing module to `hidden_imports` list in `compile_portable.py` |

---

## Contributing

This is an open-source reverse-engineering effort maintained by the GitReverse community.

- **Do not** submit pull requests that circumvent platform Terms of Service or add aggressive scraping bypasses that could lead to IP bans for end-users.
- **Do** submit endpoint patches, regex pattern updates, and shipping-rule corrections with references to the official public documentation pages.
- **Do** improve UI/UX, threading robustness, and error handling.

---

## License

Released under the MIT License. See `LICENSE` file for full text.

---

## Credits

- **GitReverse Advanced Multi-File Architecture Deployment** — framework and modular compilation methodology.
- **CustomTkinter** — native dark-theme GUI framework.
- **Community spreadsheet maintainers** — for publishing public CSV streams.

---

*Last updated: 2026-07-21 | Project Code: AGENT-HAUL-OS-STABLE | Release: v1.0.0 Stable*
