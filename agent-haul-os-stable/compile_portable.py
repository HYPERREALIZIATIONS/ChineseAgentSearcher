#!/usr/bin/env python3
"""
compile_portable.py
Automation script to compile the Agent Haul OS modular project into a single portable
executable using PyInstaller. Binds source directories via --add-data and configures
hidden imports for customtkinter, pandas, and PIL.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path


# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
SPEC_DIR = PROJECT_ROOT / "spec"


# ---------------------------------------------------------------------------
# Asset / data directories to bind into the executable
# ---------------------------------------------------------------------------
DATA_DIRS = [
    PROJECT_ROOT / "config",
    PROJECT_ROOT / "core",
    PROJECT_ROOT / "ui",
]

# Hidden imports that PyInstaller often misses with these libraries
HIDDEN_IMPORTS = [
    "customtkinter",
    "customtkinter.windows",
    "customtkinter.macos",
    "PIL",
    "PIL._tkinter_finder",
    "pandas",
    "pandas._libs",
    "requests",
    "bs4",
    "bs4.builder",
    "core.spreadsheet_parser",
    "core.image_search_engine",
    "core.shipping_calculator",
    "core.url_unmasker",
    "ui.layout",
    "ui.search_panel",
    "ui.freight_matrix",
    "config.settings",
]


# ---------------------------------------------------------------------------
# Build --add-data arguments in the format required by PyInstaller
# Format on Windows uses semicolon separator; on Unix uses colon separator.
# PyInstaller accepts OS-specific separator internally when passed via
# the standard 'source;dest' string format.
# ---------------------------------------------------------------------------
def build_add_data_args() -> list:
    args = []
    for data_dir in DATA_DIRS:
        if not data_dir.exists():
            print(f"[WARN] Data directory not found, skipping: {data_dir}")
            continue
        # PyInstaller expects "source_path;dest_relative_path_in_bundle"
        # On Windows the separator is ';', on Unix ':' — but PyInstaller's
        # argument parser handles the standard separator automatically when
        # passed as a single string with the OS-native separator.
        sep = os.pathsep
        arg = f"{data_dir}{sep}."
        args.extend(["--add-data", arg])
    return args


# ---------------------------------------------------------------------------
# Clean previous build artifacts
# ---------------------------------------------------------------------------
def clean_build_dirs():
    for directory in [DIST_DIR, BUILD_DIR, SPEC_DIR]:
        if directory.exists():
            print(f"[CLEAN] Removing {directory}")
            shutil.rmtree(directory, ignore_errors=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Determine executable name and icon
# ---------------------------------------------------------------------------
def get_executable_name() -> str:
    system = platform.system()
    if system == "Windows":
        return "HaulX.exe"
    elif system == "Darwin":
        return "HaulX.app"
    else:
        return "HaulX"


def get_pyinstaller_mode() -> list:
    # --onedir is more stable for debugging; --onefile is more portable.
    # Default to --onedir for stability, but allow override via env var.
    if os.environ.get("AGENT_HAUL_OS_ONEFILE", "0") == "1":
        return ["--onefile"]
    return ["--onedir"]


# ---------------------------------------------------------------------------
# Run PyInstaller
# ---------------------------------------------------------------------------
def run_pyinstaller():
    entry_point = PROJECT_ROOT / "main_desktop.py"
    if not entry_point.exists():
        print(f"[ERROR] Entry point not found: {entry_point}")
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(entry_point),
        "--name",
        get_executable_name(),
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--specpath",
        str(SPEC_DIR),
        "--noconfirm",
    ]

    # Add mode flags
    cmd.extend(get_pyinstaller_mode())

    # Windowed mode on Windows/macOS (no console); console on Linux
    system = platform.system()
    if system in ("Windows", "Darwin"):
        cmd.append("--windowed")
    else:
        cmd.append("--console")

    # Add hidden imports
    for hidden in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden])

    # Add data directories
    cmd.extend(build_add_data_args())

    # Icon (optional, relative to project root)
    icon_path = PROJECT_ROOT / "assets" / "icon.ico"
    if system == "Windows" and icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    elif system == "Darwin":
        icon_path = PROJECT_ROOT / "assets" / "icon.icns"
        if icon_path.exists():
            cmd.extend(["--icon", str(icon_path)])

    print("=" * 70)
    print("AGENT HAUL OS — Portable Compilation")
    print("=" * 70)
    print(f"Project Root : {PROJECT_ROOT}")
    print(f"Entry Point  : {entry_point}")
    print(f"Target Name  : {get_executable_name()}")
    print(f"Mode         : {'--onefile' if '--onefile' in cmd else '--onedir'}")
    print(f"Platform     : {system} {platform.machine()}")
    print("-" * 70)
    print("Executing command:")
    print(" ".join(cmd))
    print("-" * 70)

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=False, text=True)

    if result.returncode != 0:
        print("\n[ERROR] PyInstaller compilation failed.")
        print("Check the output above for missing imports or build errors.")
        sys.exit(result.returncode)

    print("\n[SUCCESS] Compilation completed successfully.")
    print(f"[OUTPUT]  Portable build located in: {DIST_DIR}")
    print(f"[OUTPUT]  Executable name            : {get_executable_name()}")


# ---------------------------------------------------------------------------
# Post-build verification
# ---------------------------------------------------------------------------
def verify_build():
    exe_name = get_executable_name()
    exe_path = DIST_DIR / exe_name
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"[VERIFY] Executable found: {exe_path}")
        print(f"[VERIFY] Size: {size_mb:.2f} MB")
    else:
        # For --onedir mode, look for the executable inside a folder
        possible_dir = DIST_DIR / "AgentHaulOS"
        if possible_dir.exists() and (possible_dir / exe_name).exists():
            size_mb = (possible_dir / exe_name).stat().st_size / (1024 * 1024)
            print(f"[VERIFY] Executable found in onedir bundle: {possible_dir / exe_name}")
            print(f"[VERIFY] Size: {size_mb:.2f} MB")
        else:
            print("[WARN] Could not locate the compiled executable in dist/.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    print("Agent Haul OS Portable Compiler v1.0.0")
    print("GitReverse Stable Release Build System")
    print()

    # Ensure dependencies are available
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[ERROR] PyInstaller is not installed.")
        print("        Run: pip install pyinstaller")
        sys.exit(1)

    clean_build_dirs()
    run_pyinstaller()
    verify_build()

    print()
    print("=" * 70)
    print("Compilation pipeline complete.")
    print("You may now distribute the contents of the 'dist/' directory.")
    print("=" * 70)


if __name__ == "__main__":
    main()
