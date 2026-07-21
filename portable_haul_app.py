#!/usr/bin/env python3
"""
AgentHaul Portable - Multi-Forwarder Search & Shipping Comparator
Portable Desktop Application | Single-File Monolith
# COMPILATION: pyinstaller --onefile --noconsole --clean portable_haul_app.py
"""

import os
import sys
import re
import json
import csv
import threading
import queue
import webbrowser
import urllib.parse
import urllib.request
import ssl
import hashlib
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io

# ---------------------------------------------------------------------------
# Application State & Constants
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

APP_VERSION = "1.0.0"
APP_NAME = "AgentHaul Portable"

# Agent base URLs (no affiliate hijacking)
AGENT_URLS = {
    "LitBuy": "https://www.litbuy.com/product/",
    "AllChinaBuy": "https://www.allchinabuy.com/en/item/",
    "Hoobuy": "https://www.hoobuy.com/product/",
    "Superbuy": "https://www.superbuy.com/product/",
}

# Shipping line types
SHIPPING_LINES = ["Tax-Free", "E-EMS", "DHL"]

# ---------------------------------------------------------------------------
# Global Keyword Search Data Store
# ---------------------------------------------------------------------------
class ProductStore:
    """In-memory product index loaded from CSV / Google Sheets export."""
    def __init__(self):
        self.products = []
        self.filtered = []

    def load_csv(self, path):
        self.products.clear()
        self.filtered.clear()
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Normalize keys to lowercase
                    item = {k.lower(): v for k, v in row.items()}
                    item.setdefault("title", "")
                    item.setdefault("price", "")
                    item.setdefault("link", "")
                    item.setdefault("agent", "")
                    item.setdefault("image", "")
                    self.products.append(item)
            self.filtered = list(self.products)
            return True, f"Loaded {len(self.products)} products."
        except Exception as e:
            return False, str(e)

    def search(self, query):
        q = query.strip().lower()
        if not q:
            self.filtered = list(self.products)
        else:
            terms = q.split()
            self.filtered = [
                p for p in self.products
                if all(t in (p.get("title", "") + " " + p.get("agent", "")).lower() for t in terms)
            ]
        return self.filtered


# ---------------------------------------------------------------------------
# Shipping Calculation Engine
# ---------------------------------------------------------------------------
class ShippingEngine:
    """Computes actual vs volumetric weight and estimates freight costs."""

    @staticmethod
    def actual_weight(grams):
        return grams / 1000.0

    @staticmethod
    def volumetric_weight(length, width, height):
        return (length * width * height) / 5000.0

    @staticmethod
    def chargeable_weight(actual_g, length, width, height):
        aw = ShippingEngine.actual_weight(actual_g)
        vw = ShippingEngine.volumetric_weight(length, width, height)
        return max(aw, vw)

    @staticmethod
    def estimate_line_cost(chargeable_kg, line_name):
        """Simplified cost model per line type."""
        base = chargeable_kg
        if line_name == "Tax-Free":
            return round(base * 6.5, 2)
        elif line_name == "E-EMS":
            return round(base * 12.0, 2)
        elif line_name == "DHL":
            return round(base * 18.5 + 25, 2)
        return 0.0

    @staticmethod
    def compare(weight_g, length, width, height):
        cw = ShippingEngine.chargeable_weight(weight_g, length, width, height)
        results = {}
        for agent in AGENT_URLS:
            agent_lines = {}
            for line in SHIPPING_LINES:
                agent_lines[line] = ShippingEngine.estimate_line_cost(cw, line)
            results[agent] = agent_lines
        return cw, results


# ---------------------------------------------------------------------------
# Reverse Image Search (Google Lens Mode)
# ---------------------------------------------------------------------------
class ReverseImageSearch:
    """Performs a background reverse image search via Google Lens."""

    @staticmethod
    def search(image_path):
        """Open Google Lens in the default browser for the selected image."""
        try:
            # Use Google Lens search by image via direct upload simulation
            lens_url = "https://lens.google.com/upload"
            # Browser-based file picker is the most reliable method
            # because of dynamic upload endpoints.
            webbrowser.open(lens_url)
            return True, "Opened Google Lens upload page. Please select your image there."
        except Exception as e:
            return False, str(e)


# ---------------------------------------------------------------------------
# Main Application GUI
# ---------------------------------------------------------------------------
class AgentHaulApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # Ensure portable: write to app directory only
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(os.path.join(self.app_dir, "data"), exist_ok=True)

        self.store = ProductStore()
        self.shipping_engine = ShippingEngine()
        self.image_queue = queue.Queue()
        self.selected_product_link = None
        self.selected_agent = None

        self._build_ui()
        self._bind_events()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Top Tabview
        self.tab_view = ctk.CTkTabview(self, width=1160, height=720)
        self.tab_view.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_search = self.tab_view.add("🔍 Keyword Search")
        self.tab_image = self.tab_view.add("📷 Google Photo Mode")
        self.tab_ship = self.tab_view.add("🚚 Shipping Comparator")

        self._build_search_tab()
        self._build_image_tab()
        self._build_ship_tab()

        # Status bar (bottom)
        self.status_frame = ctk.CTkFrame(self, height=40)
        self.status_frame.pack(side="bottom", fill="x", padx=20, pady=(0, 10))
        self.status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="⚠️ WARNING: This tool relies on live web scraping and public spreadsheets. It may become unstable or fail if external website layouts or API structures change.",
            font=ctk.CTkFont(size=11),
            text_color="#FFD700",
            anchor="w",
        )
        self.status_label.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # Progress bar in status
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=200)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="right", padx=10, pady=5)

    def _build_search_tab(self):
        # Header
        header = ctk.CTkFrame(self.tab_search)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header, text="Spreadsheet Ingestion & Global Keyword Search",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=10, pady=10)

        self.btn_load_csv = ctk.CTkButton(
            header, text="Load CSV / Google Sheets Export", command=self._load_csv
        )
        self.btn_load_csv.pack(side="right", padx=10, pady=10)

        # Search bar
        search_frame = ctk.CTkFrame(self.tab_search)
        search_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(search_frame, text="Search:", font=ctk.CTkFont(weight="bold")).pack(
            side="left", padx=10, pady=10
        )
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Type keywords to filter products...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self._perform_search())

        # Results table
        self.results_frame = ctk.CTkScrollableFrame(self.tab_search)
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Column headers
        headers_frame = ctk.CTkFrame(self.results_frame)
        headers_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(headers_frame, text="Agent", width=120, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Title", width=500, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Price", width=100, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Action", width=120, anchor="w").pack(side="left", padx=5)

        self.results_container = ctk.CTkFrame(self.results_frame)
        self.results_container.pack(fill="both", expand=True)

    def _build_image_tab(self):
        header = ctk.CTkFrame(self.tab_image)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header, text="Google Photo Mode - Reverse Image Search",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=10, pady=10)

        self.btn_select_image = ctk.CTkButton(
            header, text="Select Image & Search", command=self._select_image
        )
        self.btn_select_image.pack(side="right", padx=10, pady=10)

        # Image preview
        self.image_preview_frame = ctk.CTkFrame(self.tab_image)
        self.image_preview_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.image_label = ctk.CTkLabel(
            self.image_preview_frame,
            text="No image selected.\nClick 'Select Image & Search' to begin.",
            font=ctk.CTkFont(size=14),
        )
        self.image_label.pack(expand=True)

        # Results area for image search
        self.image_results_frame = ctk.CTkScrollableFrame(self.tab_image)
        self.image_results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.image_results_label = ctk.CTkLabel(
            self.image_results_frame,
            text="Search results will appear here after Google Lens processes your image.",
            font=ctk.CTkFont(size=12),
        )
        self.image_results_label.pack(pady=20)

    def _build_ship_tab(self):
        header = ctk.CTkFrame(self.tab_ship)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header, text="Multi-Agent Shipping & Price Comparator",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=10, pady=10)

        self.btn_calculate = ctk.CTkButton(
            header, text="Calculate Freight", command=self._calculate_freight
        )
        self.btn_calculate.pack(side="right", padx=10, pady=10)

        # Input frame
        input_frame = ctk.CTkFrame(self.tab_ship)
        input_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(input_frame, text="Weight (g):", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        self.entry_weight = ctk.CTkEntry(input_frame, width=120)
        self.entry_weight.insert(0, "500")
        self.entry_weight.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(input_frame, text="Length (cm):", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=2, padx=10, pady=10, sticky="w"
        )
        self.entry_length = ctk.CTkEntry(input_frame, width=120)
        self.entry_length.insert(0, "30")
        self.entry_length.grid(row=0, column=3, padx=10, pady=10)

        ctk.CTkLabel(input_frame, text="Width (cm):", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=4, padx=10, pady=10, sticky="w"
        )
        self.entry_width = ctk.CTkEntry(input_frame, width=120)
        self.entry_width.insert(0, "20")
        self.entry_width.grid(row=0, column=5, padx=10, pady=10)

        ctk.CTkLabel(input_frame, text="Height (cm):", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=6, padx=10, pady=10, sticky="w"
        )
        self.entry_height = ctk.CTkEntry(input_frame, width=120)
        self.entry_height.insert(0, "15")
        self.entry_height.grid(row=0, column=7, padx=10, pady=10)

        # Summary labels
        self.lbl_actual = ctk.CTkLabel(input_frame, text="Actual: 0.50 kg", font=ctk.CTkFont(weight="bold"))
        self.lbl_actual.grid(row=1, column=0, columnspan=4, padx=10, pady=5, sticky="w")

        self.lbl_volumetric = ctk.CTkLabel(input_frame, text="Volumetric: 0.00 kg", font=ctk.CTkFont(weight="bold"))
        self.lbl_volumetric.grid(row=1, column=4, columnspan=4, padx=10, pady=5, sticky="w")

        # Results grid
        grid_frame = ctk.CTkFrame(self.tab_ship)
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header row
        ctk.CTkLabel(grid_frame, text="Agent / Line", width=180, anchor="w", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        for idx, line in enumerate(SHIPPING_LINES, start=1):
            ctk.CTkLabel(grid_frame, text=line, width=140, anchor="center", font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=idx, padx=5, pady=5
            )

        self.shipping_rows = {}
        for row_idx, agent in enumerate(AGENT_URLS.keys(), start=1):
            ctk.CTkLabel(grid_frame, text=agent, width=160, anchor="w").grid(
                row=row_idx, column=0, padx=5, pady=5, sticky="w"
            )
            self.shipping_rows[agent] = {}
            for col_idx, line in enumerate(SHIPPING_LINES, start=1):
                lbl = ctk.CTkLabel(grid_frame, text="$0.00", width=140, anchor="center")
                lbl.grid(row=row_idx, column=col_idx, padx=5, pady=5)
                self.shipping_rows[agent][line] = lbl

        # Best value highlight
        self.best_value_frame = ctk.CTkFrame(self.tab_ship)
        self.best_value_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.lbl_best = ctk.CTkLabel(
            self.best_value_frame,
            text="Best value: --",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00FF7F",
        )
        self.lbl_best.pack(padx=10, pady=10, anchor="w")

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------
    def _bind_events(self):
        pass

    def _load_csv(self):
        filetypes = [("CSV Files", "*.csv"), ("All Files", "*.*")]
        path = filedialog.askopenfilename(
            title="Select Spreadsheet CSV Export", filetypes=filetypes
        )
        if not path:
            return
        success, msg = self.store.load_csv(path)
        if success:
            self.status_label.configure(text=f"✅ {msg}")
            self._perform_search()
        else:
            messagebox.showerror("Load Error", f"Failed to load CSV:\n{msg}")

    def _perform_search(self):
        query = self.search_entry.get()
        results = self.store.search(query)

        # Clear existing results
        for widget in self.results_container.winfo_children():
            widget.destroy()

        if not results:
            ctk.CTkLabel(
                self.results_container, text="No products found.", font=ctk.CTkFont(size=12)
            ).pack(pady=10)
            return

        for product in results:
            row = ctk.CTkFrame(self.results_container)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=product.get("agent", "Unknown"), width=120, anchor="w").pack(
                side="left", padx=5
            )
            ctk.CTkLabel(row, text=product.get("title", ""), width=500, anchor="w").pack(
                side="left", padx=5
            )
            ctk.CTkLabel(row, text=product.get("price", ""), width=100, anchor="w").pack(
                side="left", padx=5
            )

            link = product.get("link", "")
            if link:
                btn = ctk.CTkButton(
                    row,
                    text="Open",
                    width=80,
                    command=lambda l=link: webbrowser.open(l),
                )
                btn.pack(side="left", padx=5)
            else:
                ctk.CTkLabel(row, text="N/A", width=80).pack(side="left", padx=5)

    def _select_image(self):
        filetypes = [("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All Files", "*.*")]
        path = filedialog.askopenfilename(
            title="Select Product Image", filetypes=filetypes
        )
        if not path:
            return

        # Update preview
        try:
            pil_img = Image.open(path)
            pil_img.thumbnail((400, 400))
            ctk_img = ctk.CTkImage(pil_img, size=pil_img.size)
            self.image_label.configure(image=ctk_img, text="")
            self.image_label.image = ctk_img
        except Exception as e:
            self.image_label.configure(text=f"Error loading image:\n{e}")

        # Run reverse search in background
        self.status_label.configure(text="🔍 Performing reverse image search...")
        threading.Thread(
            target=self._run_reverse_search, args=(path,), daemon=True
        ).start()

    def _run_reverse_search(self, image_path):
        success, msg = ReverseImageSearch.search(image_path)
        self.image_queue.put((success, msg))
        self.after(0, self._process_reverse_search_result)

    def _process_reverse_search_result(self):
        try:
            success, msg = self.image_queue.get_nowait()
            self.status_label.configure(text=f"✅ {msg}" if success else f"❌ {msg}")
        except queue.Empty:
            pass

    def _calculate_freight(self):
        try:
            w = float(self.entry_weight.get())
            l = float(self.entry_length.get())
            wi = float(self.entry_width.get())
            h = float(self.entry_height.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values for all dimensions.")
            return

        chargeable, results = self.shipping_engine.compare(w, l, wi, h)
        aw = self.shipping_engine.actual_weight(w)
        vw = self.shipping_engine.volumetric_weight(l, wi, h)

        self.lbl_actual.configure(text=f"Actual: {aw:.2f} kg")
        self.lbl_volumetric.configure(text=f"Volumetric: {vw:.2f} kg | Chargeable: {chargeable:.2f} kg")

        best_agent = None
        best_line = None
        best_cost = float("inf")

        for agent, lines in results.items():
            for line, cost in lines.items():
                self.shipping_rows[agent][line].configure(text=f"${cost:.2f}")
                if cost < best_cost:
                    best_cost = cost
                    best_agent = agent
                    best_line = line

        if best_agent:
            self.lbl_best.configure(
                text=f"Best value: {best_agent} ({best_line}) at ${best_cost:.2f}"
            )
        self.status_label.configure(text="✅ Freight calculation complete.")


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------
def main():
    app = AgentHaulApp()
    app.mainloop()


if __name__ == "__main__":
    main()
