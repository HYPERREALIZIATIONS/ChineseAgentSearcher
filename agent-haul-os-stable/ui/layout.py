"""
ui/layout.py
CustomTkinter base window assembly, dark-theme settings, and status bars.
Constructs a native, hardware-accelerated dark theme desktop GUI with
CustomTkinter, featuring real-time sliders, scrolling result panels, action
buttons triggering native webbrowser.open() routing, and a permanent warning
label in the footer layout.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import webbrowser
import threading
import logging
from typing import Optional, Dict, List, Any, Callable

from config.settings import UI_THEME, APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Theme Initialization
# ---------------------------------------------------------------------------
def initialize_theme():
    """Set CustomTkinter appearance mode and default color theme."""
    ctk.set_appearance_mode(UI_THEME.get("mode", "Dark"))
    ctk.set_default_color_theme("blue")
    return UI_THEME


# ---------------------------------------------------------------------------
# Custom Scrollable Frame with forced dark background
# ---------------------------------------------------------------------------
class DarkScrollableFrame(ctk.CTkScrollableFrame):
    """Scrollable frame that enforces the dark theme background."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", ("#1a1a1a", "#1a1a1a"))
        kwargs.setdefault("scrollbar_button_color", UI_THEME.get("secondary_color", "#144870"))
        kwargs.setdefault("scrollbar_button_hover_color", UI_THEME.get("primary_color", "#1f6aa5"))
        super().__init__(master, **kwargs)


# ---------------------------------------------------------------------------
# Main Application Window
# ---------------------------------------------------------------------------
class MainWindow(ctk.CTk):
    """
    Primary application window. Assembles the sidebar, main content area,
    search panel, freight matrix, and footer status bar.
    """

    def __init__(self, title: str = APP_NAME):
        super().__init__()

        self.title(f"{title} v{APP_VERSION}")
        self.geometry(
            f"{UI_THEME.get('window_width', 1280)}x{UI_THEME.get('window_height', 800)}"
        )
        self.minsize(1024, 700)

        # Theme
        self.theme = initialize_theme()

        # State
        self._status_var = tk.StringVar(value="Ready")
        self._warning_var = tk.StringVar(
            value="⚠️ WARNING: External endpoints may break without notice."
        )
        self._search_callbacks: List[Callable] = []
        self._freight_callbacks: List[Callable] = []

        # Grid layout: sidebar | main_area | footer
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._build_sidebar()
        self._build_main_area()
        self._build_footer()

    # -----------------------------------------------------------------------
    # Sidebar
    # -----------------------------------------------------------------------
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=UI_THEME.get("sidebar_width", 220), corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(5, weight=1)

        # Logo / Title
        logo_label = ctk.CTkLabel(
            sidebar,
            text=APP_NAME,
            font=ctk.CTkFont(
                family=UI_THEME.get("font_family", "Segoe UI"),
                size=UI_THEME.get("font_size_title", 20),
                weight="bold",
            ),
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        version_label = ctk.CTkLabel(
            sidebar,
            text=f"v{APP_VERSION} {APP_VERSION}",
            font=ctk.CTkFont(
                family=UI_THEME.get("font_family", "Segoe UI"),
                size=UI_THEME.get("font_size_small", 11),
            ),
            text_color=UI_THEME.get("text_color_secondary", "#aaaaaa"),
        )
        version_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Navigation buttons
        self.nav_search_btn = ctk.CTkButton(
            sidebar,
            text="Search Panel",
            fg_color=UI_THEME.get("primary_color", "#1f6aa5"),
            hover_color=UI_THEME.get("secondary_color", "#144870"),
            anchor="w",
            command=lambda: self._switch_tab("search"),
        )
        self.nav_search_btn.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.nav_freight_btn = ctk.CTkButton(
            sidebar,
            text="Freight Matrix",
            fg_color="transparent",
            border_width=1,
            text_color=UI_THEME.get("text_color", "#ffffff"),
            hover_color=UI_THEME.get("secondary_color", "#144870"),
            anchor="w",
            command=lambda: self._switch_tab("freight"),
        )
        self.nav_freight_btn.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.nav_url_btn = ctk.CTkButton(
            sidebar,
            text="URL Unmasker",
            fg_color="transparent",
            border_width=1,
            text_color=UI_THEME.get("text_color", "#ffffff"),
            hover_color=UI_THEME.get("secondary_color", "#144870"),
            anchor="w",
            command=lambda: self._switch_tab("url"),
        )
        self.nav_url_btn.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # Appearance mode selector
        appearance_label = ctk.CTkLabel(
            sidebar,
            text="Appearance Mode",
            font=ctk.CTkFont(
                family=UI_THEME.get("font_family", "Segoe UI"),
                size=UI_THEME.get("font_size_small", 11),
            ),
        )
        appearance_label.grid(row=6, column=0, padx=20, pady=(10, 5), sticky="w")

        self.appearance_mode_menu = ctk.CTkOptionMenu(
            sidebar,
            values=["System", "Dark", "Light"],
            command=self._change_appearance_mode_event,
        )
        self.appearance_mode_menu.set(UI_THEME.get("mode", "Dark"))
        self.appearance_mode_menu.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")

    # -----------------------------------------------------------------------
    # Main Content Area
    # -----------------------------------------------------------------------
    def _build_main_area(self):
        self.main_container = ctk.CTkFrame(self, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Search Tab
        self.search_tab = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.search_tab.grid_rowconfigure(0, weight=1)
        self.search_tab.grid_columnconfigure(0, weight=1)
        self.search_tab.grid(row=0, column=0, sticky="nsew")

        # Freight Matrix Tab
        self.freight_tab = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.freight_tab.grid_rowconfigure(0, weight=1)
        self.freight_tab.grid_columnconfigure(0, weight=1)
        self.freight_tab.grid(row=0, column=0, sticky="nsew")
        self.freight_tab.grid_remove()

        # URL Unmasker Tab
        self.url_tab = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.url_tab.grid_rowconfigure(0, weight=1)
        self.url_tab.grid_columnconfigure(0, weight=1)
        self.url_tab.grid(row=0, column=0, sticky="nsew")
        self.url_tab.grid_remove()

        self._current_tab = "search"

    # -----------------------------------------------------------------------
    # Footer / Status Bar
    # -----------------------------------------------------------------------
    def _build_footer(self):
        footer = ctk.CTkFrame(self, height=UI_THEME.get("status_bar_height", 30), corner_radius=0)
        footer.grid(row=1, column=0, columnspan=2, sticky="ew")
        footer.grid_propagate(False)

        footer.grid_columnconfigure(1, weight=1)

        # Status label
        self.status_label = ctk.CTkLabel(
            footer,
            textvariable=self._status_var,
            font=ctk.CTkFont(
                family=UI_THEME.get("font_family", "Segoe UI"),
                size=UI_THEME.get("font_size_small", 11),
            ),
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, padx=15, pady=5, sticky="w")

        # Permanent warning label
        self.warning_label = ctk.CTkLabel(
            footer,
            textvariable=self._warning_var,
            font=ctk.CTkFont(
                family=UI_THEME.get("font_family", "Segoe UI"),
                size=UI_THEME.get("font_size_small", 11),
                weight="bold",
            ),
            text_color="#ff6b6b",
            anchor="e",
        )
        self.warning_label.grid(row=0, column=1, padx=15, pady=5, sticky="e")

    # -----------------------------------------------------------------------
    # Tab Switching
    # -----------------------------------------------------------------------
    def _switch_tab(self, tab_name: str):
        self._current_tab = tab_name
        if tab_name == "search":
            self.search_tab.grid()
            self.freight_tab.grid_remove()
            self.url_tab.grid_remove()
            self.nav_search_btn.configure(
                fg_color=UI_THEME.get("primary_color", "#1f6aa5")
            )
            self.nav_freight_btn.configure(fg_color="transparent")
            self.nav_url_btn.configure(fg_color="transparent")
        elif tab_name == "freight":
            self.search_tab.grid_remove()
            self.freight_tab.grid()
            self.url_tab.grid_remove()
            self.nav_search_btn.configure(fg_color="transparent")
            self.nav_freight_btn.configure(
                fg_color=UI_THEME.get("primary_color", "#1f6aa5")
            )
            self.nav_url_btn.configure(fg_color="transparent")
        elif tab_name == "url":
            self.search_tab.grid_remove()
            self.freight_tab.grid_remove()
            self.url_tab.grid()
            self.nav_search_btn.configure(fg_color="transparent")
            self.nav_freight_btn.configure(fg_color="transparent")
            self.nav_url_btn.configure(
                fg_color=UI_THEME.get("primary_color", "#1f6aa5")
            )

    def _change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        UI_THEME["mode"] = new_appearance_mode

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def set_status(self, message: str):
        """Update the footer status text."""
        self._status_var.set(message)

    def set_warning(self, message: str):
        """Update the permanent warning text."""
        self._warning_var.set(message)

    def get_current_tab(self) -> str:
        return self._current_tab

    def open_browser(self, url: str):
        """Open a URL in the system's default web browser."""
        if url:
            webbrowser.open(url)
