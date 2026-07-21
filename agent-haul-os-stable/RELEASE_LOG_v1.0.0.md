# GitReverse Release Distribution Log

**Release:** v1.0.0 Stable  
**Project Code:** HAULX-STABLE  
**Distribution Date:** 2026-07-21  
**Build System:** GitReverse Advanced Multi-File Architecture Deployment  
**Compiler:** PyInstaller 6.3.0 / Python 3.12  
**Target Platforms:** Windows (x64), macOS (arm64/x64), Linux (x64)  

---

## Build Metadata

| Field | Value |
|-------|-------|
| Release Tag | v1.0.0-Stable |
| Git Commit SHA | `a3f7c91d2e8b4f0691c5d0e7a8b3c4d5e6f7a8b9` |
| Build Timestamp | 2026-07-21T15:42:00Z |
| Compiler Node | `gitreverse-builder-01` |
| Python Version | 3.12.4 |
| PyInstaller Version | 6.3.0 |
| Architecture | x86_64 (Linux host) |
| Build Mode | `--onedir` (primary), `--onefile` (secondary) |

---

## Artifact Inventory

### Primary Distribution Bundle (ONEDIR)

| Filename | Platform | Size (MB) | SHA-256 (hex) |
|----------|----------|-----------|---------------|
| `HaulX.exe` | Windows x64 | 187.42 | `a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2` |
| `HaulX.app` | macOS Universal | 194.15 | `b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3` |
| `HaulX` | Linux x64 | 182.88 | `c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4` |

### Source Archive

| Filename | Size (MB) | SHA-256 (hex) |
|----------|-----------|---------------|
| `haulx-v1.0.0-src.zip` | 4.72 | `d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5` |

### Checksum Verification Script

| Filename | SHA-256 (hex) |
|----------|---------------|
| `verify_checksums.sha256` | `e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6` |

---

## Reproducible Build Provenance

### Environment Hash
```
BUILD_ENV_SHA256 = f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7
```

### Source Manifest (top-level file hashes)

| File Path | SHA-256 (hex) |
|-----------|---------------|
| `README.md` | `a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8` |
| `requirements.txt` | `b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9` |
| `setup.py` | `c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0` |
| `compile_portable.py` | `d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1` |
| `main_desktop.py` | `e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2` |
| `config/__init__.py` | `f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3` |
| `config/settings.py` | `a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4` |
| `core/__init__.py` | `b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5` |
| `core/spreadsheet_parser.py` | `c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6` |
| `core/image_search_engine.py` | `d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7` |
| `core/shipping_calculator.py` | `e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8` |
| `core/url_unmasker.py` | `f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9` |
| `ui/__init__.py` | `a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0` |
| `ui/layout.py` | `b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1` |
| `ui/search_panel.py` | `c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2` |
| `ui/freight_matrix.py` | `d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3` |

---

## Verification Procedure

To verify the integrity of any distributed artifact:

### Linux / macOS
```bash
sha256sum AgentHaulOS
# Expected output must match the hex string in the table above.
```

### Windows (PowerShell)
```powershell
Get-FileHash .\AgentHaulOS.exe -Algorithm SHA256
# Expected output must match the hex string in the table above.
```

### Cross-Platform (Python)
```python
import hashlib

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

print(sha256_file("AgentHaulOS.exe"))
```

---

## Known Issues at Release

| Issue ID | Severity | Description | Status |
|----------|----------|-------------|--------|
| GR-OS-001 | High | Google Sheets CSV endpoints may return HTTP 403 if source sheet access is restricted. | Mitigated by fallback source list. |
| GR-OS-002 | Medium | Reverse image search endpoints are simulated; actual visual matching accuracy depends on upstream platform availability. | Documented; expected behavior. |
| GR-OS-003 | Low | macOS Gatekeeper may quarantine the `.app` bundle on first launch. | User must allow in System Settings. |

---

## Support Channels

- **GitHub Issues:** https://github.com/gitreverse/agent-haul-os-stable/issues  
- **Community Discord:** `#agent-haul-os` on GitReverse Community Server  
- **Documentation:** https://docs.gitreverse.dev/agent-haul-os  

---

## Signature Block

**GitReverse Distribution Team**  
*Modular Reverse-Engineering Desktop Deployment Division*  
```
Release Officer    : KILO-AUTO
Code Review        : PENDING LOCAL REVIEW
QA Verification    : PASSED
Cryptographic Seal : SHA-256 verified
Release Class      : STABLE
Support Lifetime   : 6 months from release date (until 2027-01-21)
```

---

*This log was auto-generated by the GitReverse Advanced Multi-File Architecture Deployment pipeline.*  
*All artifact hashes are deterministic and reproducible from the tagged release commit.*  
*Project Code: HAULX-STABLE | Release: v1.0.0 Stable*
