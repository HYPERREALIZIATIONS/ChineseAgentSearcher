# GitHub Releases - AgentHaul Portable

## v1.0.0 - Production Stable (Experimental Image Search)

**Release Date:** 2026-07-21  
**Status:** Production Stable — Image Search marked as Experimental  
**Notes:** Initial production release. Reverse image search uses browser-based Google Lens fallback due to dynamic upload endpoints.

---

### 📥 Downloads

| Platform | Download | SHA-256 |
|----------|----------|---------|
| Windows x64 | [AgentHaul-Portable-Windows-x64.exe](https://github.com/your-repo/AgentHaul-Portable/releases/download/v1.0.0/AgentHaul-Portable-Windows-x64.exe) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| macOS Universal | [AgentHaul-Portable-macOS.dmg](https://github.com/your-repo/AgentHaul-Portable/releases/download/v1.0.0/AgentHaul-Portable-macOS.dmg) | `a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a` |

> ⚠️ **Beta Warning:** This release is stable for CSV search and shipping comparison, but the **Google Photo Mode (Reverse Image Search)** is experimental. It relies on Google Lens's public browser interface, which may change without notice. If image search breaks, update to the latest version or use the browser-based Google Lens directly.

---

### Integrity Verification

Verify your download using the SHA-256 hashes below.

#### Windows x64 (`AgentHaul-Portable-Windows-x64.exe`)

```text
SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Size:    ~45 MB (onefile bundle with Python runtime + CustomTkinter)
Built:   2026-07-21
Compiler: PyInstaller 6.x
Python:  3.11.x embedded
```

#### macOS Universal (`AgentHaul-Portable-macOS.dmg`)

```text
SHA-256: a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a
Size:    ~52 MB (onefile bundle with Python runtime + CustomTkinter)
Built:   2026-07-21
Compiler: PyInstaller 6.x
Python:  3.11.x embedded
```

**Verification Command (macOS / Linux):**

```bash
shasum -a 256 AgentHaul-Portable-Windows-x64.exe
shasum -a 256 AgentHaul-Portable-macOS.dmg
```

**Verification Command (Windows PowerShell):**

```powershell
Get-FileHash AgentHaul-Portable-Windows-x64.exe -Algorithm SHA256
Get-FileHash AgentHaul-Portable-macOS.dmg -Algorithm SHA256
```

---

### What's New in v1.0.0

- ✨ **Global Keyword Search:** Load any CSV spreadsheet and filter products in real-time.
- ✨ **Multi-Agent Shipping Comparator:** Side-by-side Tax-Free / E-EMS / DHL cost estimates for LitBuy, AllChinaBuy, Hoobuy, and Superbuy.
- ✨ **Google Photo Mode:** Browser-based reverse image search integration via Google Lens.
- ✨ **Portable Architecture:** Single-file executable, no installation required.
- ✨ **Dark-Mode GUI:** Built with CustomTkinter for a native, modern look.
- ⚠️ **Instability Warning:** Live web scraping may break if external sites change their structure.

---

### Known Limitations

- Reverse image search uses a browser redirect to Google Lens; direct API-based search is not available due to Google's dynamic endpoints.
- Shipping cost estimates are based on simplified public rate models and may not reflect exact agent quotes.
- CSV parsing requires standard column headers: `title`, `price`, `link`, `agent`.

---

### Installation (if not using portable binary)

```bash
# 1. Clone the repo
git clone https://github.com/your-repo/AgentHaul-Portable.git
cd AgentHaul-Portable

# 2. Install dependencies
pip install customtkinter pillow

# 3. Run
python portable_haul_app.py
```

---

### Compilation from Source

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --clean portable_haul_app.py
```

The compiled binary will appear in `dist/`.

---

### Support & Community

- **Issues:** [GitHub Issues](https://github.com/your-repo/AgentHaul-Portable/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-repo/AgentHaul-Portable/discussions)

*AgentHaul Portable is not affiliated with LitBuy, AllChinaBuy, Hoobuy, or Superbuy. All trademarks belong to their respective owners.*
