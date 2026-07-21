# ⚠️ BETA / INSTABILITY WARNING ⚠️

**AgentHaul Portable is currently in BETA (v1.0.0 Experimental).**

Because this application hooks into **live, third-party web structures** — including **Google Lens data extraction** and **shifting agent logistics web pages** — its functions **might break or become unstable without notice** when external platforms update their layouts, API endpoints, or access policies.

**Do not use this tool as your sole source of truth for pricing or shipping.** Always verify costs directly on the agent's website before submitting a haul. The developers assume no liability for financial loss, missed deals, or incorrect shipping estimates arising from web-structure changes.

---

# AgentHaul Portable

**AgentHaul Portable** is an open-source, single-file desktop application that solves two massive frustrations in the proxy-shopping community:

1. **The extreme difficulty of finding specific fashion products** across hundreds of unorganized, slow community spreadsheets.
2. **The inability to accurately compare product prices and international shipping freight costs side-by-side** across competing agents (LitBuy, AllChinaBuy, Hoobuy, Superbuy) before submitting a haul.

Stop copy-pasting links between ten browser tabs and blindly guessing shipping costs. AgentHaul Portable brings global keyword search, reverse image search, and multi-agent freight comparison into one lightweight, portable desktop app.

---

## Features Guide

### 1. Global Keyword Search (Spreadsheet Ingestion)

Community product spreadsheets are messy. AgentHaul Portable lets you load any **CSV export** (from a public Google Sheet or community spreadsheet) and instantly filter it.

- Click **"Load CSV / Google Sheets Export"** to import your spreadsheet.
- Type any keyword (e.g., "stone island hoodie", "yeezy 350", "denim jacket") into the search bar.
- The app filters results in real-time across **title** and **agent** fields.
- Click **"Open"** on any row to launch the product directly in your default browser — **zero affiliate link hijacking**.

### 2. Google Photo Mode (Reverse Image Search)

Found a product screenshot or photo but don't know the keywords?

- Click the **"Select Image & Search"** button.
- Choose a local image (PNG, JPG, JPEG, BMP, WEBP).
- The app displays a preview and opens **Google Lens** in your default browser.
- Upload your image there to find matching Taobao, Weidian, or 1688 listings.

> ⚠️ **Note:** Reverse image search results depend on Google Lens's public web interface. If Google changes its upload flow, this feature may temporarily break until updated.

### 3. Multi-Agent Shipping & Price Comparator Engine

Wondering how much it actually costs to ship a package from China?

1. Enter your **package metrics**:
   - **Weight (g):** Actual physical weight of the parcel.
   - **Length / Width / Height (cm):** Parcel dimensions.
2. Click **"Calculate Freight"**.
3. The engine computes:
   - **Actual Weight** (kg)
   - **Volumetric Weight** (kg)
   - **Chargeable Weight** = max(actual, volumetric)
4. A **side-by-side comparative grid** displays estimated freight costs across all four major agents for three shipping lines:
   - **Tax-Free**
   - **E-EMS**
   - **DHL**
5. The **"Best value"** banner automatically highlights the cheapest agent + line combination.
6. Use the **agent buttons** in the Keyword Search tab to open products directly in the correct agent's storefront.

> ⚠️ **Note:** Shipping estimates are based on simplified public rate models and may vary. Always confirm final pricing on the agent's checkout page.

---

## Setup & Compilation

### Prerequisites

- **Python 3.9+** installed on your machine.
- A modern operating system (Windows, macOS, or Linux).

### Step 1: Install Dependencies

Open a terminal or command prompt in the application folder and run:

```bash
pip install customtkinter pillow
```

### Step 2: Run the Application

```bash
python portable_haul_app.py
```

A dark-mode GUI window will appear. You can now load CSV spreadsheets, search products, run reverse image searches, and compare shipping costs.

### Step 3: Compile into a Portable Executable (Optional)

To distribute or run without Python installed, compile the app using PyInstaller:

```bash
pyinstaller --onefile --noconsole --clean portable_haul_app.py
```

- **`--onefile`**: Bundles everything into a single `.exe` (Windows) or binary.
- **`--noconsole`**: Runs the GUI without a visible console window.
- **`--clean`**: Cleans temporary build files before compilation.

After compilation, find the standalone executable in the `dist/` folder.

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'customtkinter'` | Run `pip install customtkinter` again. Ensure you're using the correct Python environment. |
| Image preview is blank | Ensure the selected file is a valid image format (PNG, JPG, JPEG, BMP, WEBP). |
| CSV won't load | Verify the file is UTF-8 encoded CSV with headers including at least `title`, `price`, `link`, `agent`. |
| Google Lens button doesn't work | Ensure your default browser is set correctly and has internet access. |
| Shipping costs seem wrong | These are estimates. Check the agent's official shipping calculator for exact rates. |

---

## Contributing

AgentHaul Portable is open-source and community-driven. Because it relies on live web scraping, contributions that improve rate models, spreadsheet parsing, or image-search resilience are highly encouraged.

1. Fork the repository.
2. Create a feature branch.
3. Submit a Pull Request with a clear description of changes.

---

## License

This project is released under the MIT License. See `LICENSE` for details.

---

*Built with ❤️ for the proxy-shopping community. Stay safe, verify your costs, and happy hauling.*
