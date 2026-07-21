#!/usr/bin/env python3
"""
generate_logo_assets.py
Generate HaulX logo PNGs at multiple resolutions from the SVG source.
Requires: pip install cairosvg pillow
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
SVG_PATH = os.path.join(ASSETS_DIR, "haulx_logo.svg")

SIZES = [512, 256, 128, 64, 48, 32, 16]


def generate():
    try:
        import cairosvg
    except ImportError:
        print("[ERROR] cairosvg is not installed. Run: pip install cairosvg")
        sys.exit(1)

    if not os.path.exists(SVG_PATH):
        print(f"[ERROR] SVG source not found at {SVG_PATH}")
        sys.exit(1)

    os.makedirs(ASSETS_DIR, exist_ok=True)

    for size in SIZES:
        png_path = os.path.join(ASSETS_DIR, f"haulx_logo_{size}.png")
        try:
            cairosvg.svg2png(
                url=SVG_PATH,
                write_to=png_path,
                output_width=size,
                output_height=size,
            )
            print(f"[OK] Generated {png_path}")
        except Exception as exc:
            print(f"[FAIL] Could not generate {size}px PNG: {exc}")

    # Generate Windows .ico (multi-resolution)
    try:
        from PIL import Image

        images = []
        for size in [256, 128, 64, 48, 32, 16]:
            png_path = os.path.join(ASSETS_DIR, f"haulx_logo_{size}.png")
            if os.path.exists(png_path):
                img = Image.open(png_path)
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                images.append(img)

        if images:
            ico_path = os.path.join(ASSETS_DIR, "icon.ico")
            images[0].save(
                ico_path,
                format="ICO",
                sizes=[(img.width, img.height) for img in images],
            )
            print(f"[OK] Generated {ico_path}")
    except ImportError:
        print("[WARN] Pillow not installed; skipping .ico generation.")
    except Exception as exc:
        print(f"[WARN] Could not generate .ico: {exc}")

    print("\n[DONE] Logo assets generated in assets/")


if __name__ == "__main__":
    generate()
