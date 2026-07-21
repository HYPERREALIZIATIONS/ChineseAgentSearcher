"""
ui/search_panel.py
Global text search entries and "Google Photo Mode" image upload triggers.
Provides the search panel widget embedded into the main application window.
"""

import os
import tkinter as tk
from tkinter import filedialog
from typing import Optional, List, Callable, Any

import customtkinter as ctk
from PIL import Image, ImageTk

from config.settings import UI_THEME

# ---------------------------------------------------------------------------
# Search Panel
# ---------------------------------------------------------------------------
class SearchPanel(ctk.CTkFrame):
    """
    Global text search entries and image upload trigger panel.
    Contains:
    - Keyword search entry with live search trigger
    - Category filter dropdown
    - Price range sliders
    - Image upload button (Google Photo Mode)
    - Scrollable results area
    """

    def __init__(self, master, on_search: Optional[Callable] = None, on_image_search: Optional[Callable] = None):
        super().__init__(master, fg_color="transparent")

        self.on_search = on_search
        self.on_image_search = on_image_search
        self._results: List[Any] = []
        self._selected_image_path: Optional[str] = None

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Search controls row
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        controls_frame.grid_columnconfigure(1, weight=1)

        # Keyword entry
        ctk.CTkLabel(
            controls_frame,
            text="Keyword:",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
        ).grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")

        self.keyword_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="Search category, brand, description...",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
        )
        self.keyword_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.keyword_entry.bind("<KeyRelease>", lambda e: self._trigger_search())

        # Category dropdown
        ctk.CTkLabel(
            controls_frame,
            text="Category:",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
        ).grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")

        self.category_option = ctk.CTkOptionMenu(
            controls_frame,
            values=["All", "Shoes", "Clothing", "Accessories", "Bags", "Electronics", "Watches", "Other"],
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
            command=lambda _: self._trigger_search(),
        )
        self.category_option.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.category_option.set("All")

        # Search button
        self.search_button = ctk.CTkButton(
            controls_frame,
            text="Search",
            command=self._trigger_search,
            fg_color=UI_THEME["primary_color"],
            hover_color=UI_THEME["secondary_color"],
            width=100,
        )
        self.search_button.grid(row=0, column=4, padx=(10, 5), pady=5, sticky="e")

        # Image search button
        self.image_button = ctk.CTkButton(
            controls_frame,
            text="Google Photo Mode",
            command=self._open_image_dialog,
            fg_color="#8e44ad",
            hover_color="#732d91",
            width=160,
        )
        self.image_button.grid(row=0, column=5, padx=(5, 0), pady=5, sticky="e")

        # Image preview
        self.image_preview_label = ctk.CTkLabel(
            controls_frame,
            text="No image selected",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_small"]),
            text_color=UI_THEME["text_color_secondary"],
        )
        self.image_preview_label.grid(row=1, column=0, columnspan=6, padx=5, pady=(0, 5), sticky="w")

        # Price range row
        range_frame = ctk.CTkFrame(self, fg_color="transparent")
        range_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        range_frame.grid_columnconfigure(1, weight=1)
        range_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            range_frame,
            text="Min CNY:",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_small"]),
        ).grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")

        self.min_price_entry = ctk.CTkEntry(range_frame, width=100, placeholder_text="0")
        self.min_price_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.min_price_entry.bind("<KeyRelease>", lambda e: self._trigger_search())

        ctk.CTkLabel(
            range_frame,
            text="Max CNY:",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_small"]),
        ).grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")

        self.max_price_entry = ctk.CTkEntry(range_frame, width=100, placeholder_text="99999")
        self.max_price_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.max_price_entry.bind("<KeyRelease>", lambda e: self._trigger_search())

        # Results area
        self.results_frame = DarkScrollableFrame(self, label_text="Search Results")
        self.results_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.results_frame.grid_columnconfigure(0, weight=1)

        self._no_results_label = ctk.CTkLabel(
            self.results_frame,
            text="No results yet. Enter a keyword and press Search.",
            text_color=UI_THEME["text_color_secondary"],
        )
        self._no_results_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

    # -----------------------------------------------------------------------
    # Actions
    # -----------------------------------------------------------------------
    def _trigger_search(self):
        """Collect search criteria and invoke the on_search callback."""
        if self.on_search is None:
            return
        keyword = self.keyword_entry.get().strip()
        category = self.category_option.get()
        min_price_raw = self.min_price_entry.get().strip()
        max_price_raw = self.max_price_entry.get().strip()

        try:
            min_price = float(min_price_raw) if min_price_raw else None
        except ValueError:
            min_price = None
        try:
            max_price = float(max_price_raw) if max_price_raw else None
        except ValueError:
            max_price = None

        self.on_search(keyword=keyword, category=category, min_price=min_price, max_price=max_price)

    def _open_image_dialog(self):
        """Open file dialog to select an image for Google Photo Mode."""
        file_path = filedialog.askopenfilename(
            title="Select Image for Visual Search",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.webp *.bmp *.gif"),
                ("All Files", "*.*"),
            ],
        )
        if file_path:
            self._selected_image_path = file_path
            self.image_preview_label.configure(
                text=f"Selected: {os.path.basename(file_path)}",
                text_color=UI_THEME["primary_color"],
            )
            if self.on_image_search:
                self.on_image_search(image_path=file_path)

    # -----------------------------------------------------------------------
    # Results Rendering
    # -----------------------------------------------------------------------
    def clear_results(self):
        """Remove all result cards from the scrollable frame."""
        for widget in self.results_frame.winfo_children():
            if widget != self._no_results_label:
                widget.destroy()
        self._no_results_label.grid()
        self._results = []

    def display_results(self, results: List[Any]):
        """Render a list of result items (dicts or objects) into the scrollable frame."""
        self.clear_results()
        if not results:
            self._no_results_label.configure(text="No results found.")
            self._no_results_label.grid()
            return

        self._no_results_label.grid_remove()
        for idx, result in enumerate(results):
            self._add_result_card(idx, result)

    def _add_result_card(self, index: int, result: Any):
        """Add a single result card to the results frame."""
        card = ctk.CTkFrame(self.results_frame, corner_radius=8)
        card.grid(row=index, column=0, sticky="ew", padx=5, pady=5)
        card.grid_columnconfigure(1, weight=1)

        # Extract fields
        if isinstance(result, dict):
            category = result.get("category", "")
            brand = result.get("brand", "")
            price = result.get("price_cny", "")
            link = result.get("product_link", "")
            desc = result.get("description", "")
            img_url = result.get("qc_image_url", "")
        else:
            category = getattr(result, "category", "")
            brand = getattr(result, "brand", "")
            price = getattr(result, "price_cny", "")
            link = getattr(result, "product_link", "")
            desc = getattr(result, "description", "")
            img_url = getattr(result, "qc_image_url", "")

        title_text = f"{brand or 'Unknown'} — {category or 'Uncategorized'}"
        if price not in (None, "", "None"):
            title_text += f"  ¥{price} CNY"

        title_label = ctk.CTkLabel(
            card,
            text=title_text,
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"], weight="bold"),
            anchor="w",
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        if desc:
            desc_label = ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_small"]),
                anchor="w",
                wraplength=800,
            )
            desc_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w")

        if img_url:
            img_label = ctk.CTkLabel(
                card,
                text=f"QC Image: {img_url}",
                font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_small"]),
                anchor="w",
                cursor="hand2",
                text_color=UI_THEME["primary_color"],
            )
            img_label.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")
            img_label.bind("<Button-1>", lambda e, u=img_url: self.master.open_browser(u))

        if link:
            link_btn = ctk.CTkButton(
                card,
                text="Open Product Link",
                command=lambda u=link: self.master.open_browser(u),
                fg_color="transparent",
                border_width=1,
                width=140,
                height=28,
            )
            link_btn.grid(row=2, column=1, padx=10, pady=(0, 10), sticky="e")

    def set_status_callback(self, callback: Callable[[str], None]):
        """Allow external code to set status on the parent window."""
        self._status_callback = callback
