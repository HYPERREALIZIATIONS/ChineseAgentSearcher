"""
main_desktop.py
Master project bootstrap script. Imports all modules, orchestrates thread tasks
smoothly without freezing the CustomTkinter GUI loop, and manages error propagation.
"""

import os
import sys
import logging
import threading
import traceback
import webbrowser
from typing import Optional, Dict, List, Any
from queue import Queue

# Ensure the project root is on sys.path so subpackages are importable
# when running `python main_desktop.py` from the project root.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import customtkinter as ctk

from config.settings import APP_NAME, APP_VERSION, UI_THEME
from core.spreadsheet_parser import SpreadsheetParser, ProductEntry
from core.image_search_engine import ImageSearchEngine, VisualSearchResult
from core.shipping_calculator import ShippingCalculator
from core.url_unmasker import URLUnmasker, UnmaskedURL

from ui.layout import MainWindow, initialize_theme, DarkScrollableFrame
from ui.search_panel import SearchPanel
from ui.freight_matrix import FreightMatrix

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("agent_haul_os.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("AgentHaulOS")

# ---------------------------------------------------------------------------
# Application Controller
# ---------------------------------------------------------------------------
class ApplicationController:
    """
    Orchestrates all engine threads, UI callbacks, and error propagation.
    Keeps the CustomTkinter mainloop responsive by offloading I/O to
    background threads and using queues for safe UI updates.
    """

    def __init__(self):
        self.root: Optional[ctk.CTk] = None
        self.main_window: Optional[MainWindow] = None
        self.search_panel: Optional[SearchPanel] = None
        self.freight_matrix: Optional[FreightMatrix] = None

        # Engines
        self.spreadsheet_parser = SpreadsheetParser()
        self.image_search_engine = ImageSearchEngine()
        self.shipping_calculator = ShippingCalculator()
        self.url_unmasker = URLUnmasker()

        # Thread communication queues
        self._search_result_queue: "Queue[List[ProductEntry]]" = Queue()
        self._image_result_queue: "Queue[List[VisualSearchResult]]" = Queue()
        self._freight_result_queue: "Queue[Dict[str, Any]]" = Queue()
        self._url_result_queue: "Queue[List[UnmaskedURL]]" = Queue()

        # Worker threads
        self._search_worker: Optional[threading.Thread] = None
        self._image_worker: Optional[threading.Thread] = None
        self._freight_worker: Optional[threading.Thread] = None
        self._url_worker: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Polling state
        self._poll_interval_ms = 100

    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------
    def start(self):
        """Initialize UI, wire callbacks, and start the main loop."""
        logger.info("Starting %s v%s", APP_NAME, APP_VERSION)
        initialize_theme()
        self.root = ctk.CTk()
        self.main_window = MainWindow(title=APP_NAME)
        self._build_ui()
        self._wire_callbacks()
        self._start_background_indexing()
        self._schedule_queue_polling()
        self.root.mainloop()
        logger.info("Application shutdown complete.")

    def shutdown(self):
        """Clean shutdown of all engines and threads."""
        self._stop_event.set()
        self.spreadsheet_parser.stop_async_indexing()
        self.image_search_engine.stop()
        logger.info("Shutdown signal sent to all engines.")

    # -----------------------------------------------------------------------
    # UI Assembly
    # -----------------------------------------------------------------------
    def _build_ui(self):
        assert self.main_window is not None

        # Search panel -> search tab
        self.search_panel = SearchPanel(
            self.main_window.search_tab,
            on_search=self._on_search_requested,
            on_image_search=self._on_image_search_requested,
        )
        self.search_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Freight matrix -> freight tab
        self.freight_matrix = FreightMatrix(
            self.main_window.freight_tab,
            on_calculate=self._on_freight_calculate_requested,
        )
        self.freight_matrix.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # URL Unmasker tab
        self._build_url_unmasker_tab()

        # Set initial status
        self.main_window.set_status("Ready — indexing spreadsheets in background...")
        self._url_scroll_frame: Optional[DarkScrollableFrame] = None

    def _build_url_unmasker_tab(self):
        assert self.main_window is not None

        tab = self.main_window.url_tab
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        input_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            input_frame,
            text="Paste Affiliate / Short Link:",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
        ).grid(row=0, column=0, padx=(0, 5), pady=10, sticky="w")

        self.url_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="https://bit.ly/xyz or https://agent.com/?utm_source=...",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
        )
        self.url_input.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.url_input.bind("<KeyRelease>", lambda e: self._debounce_url_unmask())

        self.url_unmask_button = ctk.CTkButton(
            input_frame,
            text="Unmask & Resolve",
            command=self._on_url_unmask_requested,
            fg_color=UI_THEME["primary_color"],
            hover_color=UI_THEME["secondary_color"],
        )
        self.url_unmask_button.grid(row=0, column=2, padx=(5, 0), pady=10, sticky="e")

        # Results
        self.url_results_frame = DarkScrollableFrame(tab, label_text="Unmasked Results")
        self.url_results_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.url_results_frame.grid_columnconfigure(0, weight=1)
        self._url_scroll_frame = self.url_results_frame

        self._url_empty_label = ctk.CTkLabel(
            self.url_results_frame,
            text="Paste a link above and click Unmask & Resolve.",
            text_color=UI_THEME["text_color_secondary"],
        )
        self._url_empty_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        self._url_debounce_timer: Optional[str] = None

    # -----------------------------------------------------------------------
    # Callback Wiring
    # -----------------------------------------------------------------------
    def _wire_callbacks(self):
        # Search callbacks
        self.search_panel.set_status_callback(self.main_window.set_status)

    # -----------------------------------------------------------------------
    # Background Indexing
    # -----------------------------------------------------------------------
    def _start_background_indexing(self):
        self.spreadsheet_parser.start_async_indexing()
        # Periodic status polling for indexing progress
        self._schedule_status_polling()

    def _schedule_status_polling(self):
        if self._stop_event.is_set():
            return
        if self.main_window and self.spreadsheet_parser:
            status = self.spreadsheet_parser.get_status()
            indexed = self.spreadsheet_parser.get_indexed_count()
            meta = status.get("_meta", "")
            self.main_window.set_status(f"Indexed {indexed} products. {meta}")
        self.root.after(2000, self._schedule_status_polling)

    # -----------------------------------------------------------------------
    # Search Flow
    # -----------------------------------------------------------------------
    def _on_search_requested(self, keyword: str, category: str, min_price: Optional[float], max_price: Optional[float]):
        """Offload search to background thread."""
        self.main_window.set_status("Searching...")
        self.search_panel.clear_results()

        if not keyword and category == "All" and min_price is None and max_price is None:
            self.main_window.set_status("Enter a keyword to search.")
            return

        def _search_worker():
            try:
                results = self.spreadsheet_parser.search(keyword, max_results=200)
                # Apply client-side filters
                filtered = []
                for entry in results:
                    if category != "All" and entry.category != category:
                        continue
                    if min_price is not None and (entry.price_cny is None or entry.price_cny < min_price):
                        continue
                    if max_price is not None and (entry.price_cny is None or entry.price_cny > max_price):
                        continue
                    filtered.append(entry)
                self._search_result_queue.put(filtered)
            except Exception as exc:
                logger.error("Search worker error: %s", exc)
                self._search_result_queue.put([])

        if self._search_worker and self._search_worker.is_alive():
            logger.warning("Search worker already running.")
            return

        self._search_worker = threading.Thread(target=_search_worker, daemon=True)
        self._search_worker.start()

    def _on_image_search_requested(self, image_path: str):
        """Offload image search to background thread."""
        self.main_window.set_status("Running visual search...")
        self.search_panel.clear_results()

        def _image_worker():
            try:
                results = self.image_search_engine.search_from_file(image_path)
                self._image_result_queue.put(results)
            except Exception as exc:
                logger.error("Image search worker error: %s", exc)
                self._image_result_queue.put([])

        if self._image_worker and self._image_worker.is_alive():
            logger.warning("Image search worker already running.")
            return

        self._image_worker = threading.Thread(target=_image_worker, daemon=True)
        self._image_worker.start()

    # -----------------------------------------------------------------------
    # Freight Flow
    # -----------------------------------------------------------------------
    def _on_freight_calculate_requested(
        self,
        length_cm: float,
        width_cm: float,
        height_cm: float,
        weight_kg: float,
        destination: str,
        item_price_cny: float,
    ):
        """Offload freight calculation to background thread."""
        self.main_window.set_status("Calculating freight...")

        def _freight_worker():
            try:
                results = self.shipping_calculator.calculate_all(
                    actual_weight_kg=weight_kg,
                    length_cm=length_cm,
                    width_cm=width_cm,
                    height_cm=height_cm,
                    destination=destination,
                    item_price_cny=item_price_cny,
                )
                self._freight_result_queue.put(results)
            except Exception as exc:
                logger.error("Freight worker error: %s", exc)
                self._freight_result_queue.put([])

        if self._freight_worker and self._freight_worker.is_alive():
            logger.warning("Freight worker already running.")
            return

        self._freight_worker = threading.Thread(target=_freight_worker, daemon=True)
        self._freight_worker.start()

    # -----------------------------------------------------------------------
    # URL Unmasker Flow
    # -----------------------------------------------------------------------
    def _on_url_unmask_requested(self):
        url = self.url_input.get().strip()
        if not url:
            self.main_window.set_status("Enter a URL to unmask.")
            return

        self.main_window.set_status("Unmasking URL...")
        self._url_empty_label.grid_remove()

        def _url_worker():
            try:
                result = self.url_unmasker.unmask(url)
                self._url_result_queue.put([result])
            except Exception as exc:
                logger.error("URL unmask worker error: %s", exc)
                self._url_result_queue.put([])

        if self._url_worker and self._url_worker.is_alive():
            logger.warning("URL worker already running.")
            return

        self._url_worker = threading.Thread(target=_url_worker, daemon=True)
        self._url_worker.start()

    def _debounce_url_unmask(self):
        """Debounce URL unmasking to avoid excessive calls while typing."""
        if self._url_debounce_timer:
            self.root.after_cancel(self._url_debounce_timer)
        self._url_debounce_timer = self.root.after(800, self._on_url_unmask_requested)

    # -----------------------------------------------------------------------
    # Queue Polling (runs on main thread via .after)
    # -----------------------------------------------------------------------
    def _schedule_queue_polling(self):
        """Periodically drain result queues and update UI on the main thread."""
        if self._stop_event.is_set():
            return

        # Drain search results
        while not self._search_result_queue.empty():
            results = self._search_result_queue.get_nowait()
            self.search_panel.display_results(results)
            self.main_window.set_status(f"Found {len(results)} results.")

        # Drain image search results
        while not self._image_result_queue.empty():
            results = self._image_result_queue.get_nowait()
            self.search_panel.display_results(results)
            self.main_window.set_status(f"Visual search returned {len(results)} results.")

        # Drain freight results
        while not self._freight_result_queue.empty():
            results = self._freight_result_queue.get_nowait()
            if results:
                # Format for freight matrix
                formatted = self._format_freight_results(results)
                self.freight_matrix.display_results(formatted)
                self.main_window.set_status("Freight calculation complete.")
            else:
                self.main_window.set_status("Freight calculation returned no data.")

        # Drain URL results
        while not self._url_result_queue.empty():
            results = self._url_result_queue.get_nowait()
            self._display_url_results(results)
            self.main_window.set_status("URL unmasking complete.")

        self.root.after(self._poll_interval_ms, self._schedule_queue_polling)

    # -----------------------------------------------------------------------
    # Result Formatting Helpers
    # -----------------------------------------------------------------------
    def _format_freight_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Reformat agent cost list into a dict keyed by agent name for the matrix."""
        formatted: Dict[str, Any] = {}
        for res in results:
            agent = res.get("agent_name", "unknown")
            formatted[agent] = res
        return formatted

    def _display_url_results(self, results: List[UnmaskedURL]):
        """Render URL unmasking results in the URL tab."""
        # Clear previous
        if self._url_scroll_frame:
            for widget in self._url_scroll_frame.winfo_children():
                if widget != self._url_empty_label:
                    widget.destroy()

        if not results:
            self._url_empty_label.configure(text="No results.")
            self._url_empty_label.grid()
            return

        self._url_empty_label.grid_remove()
        scroll = self._url_scroll_frame
        for idx, result in enumerate(results):
            card = ctk.CTkFrame(scroll, corner_radius=8)
            card.grid(row=idx, column=0, sticky="ew", padx=5, pady=5)
            card.grid_columnconfigure(1, weight=1)

            fields = [
                ("Original", result.original_url),
                ("Clean", result.clean_url),
                ("Agent", result.agent_name.upper() if result.agent_name else "N/A"),
                ("Item ID", result.item_id or "N/A"),
                ("Agent Link", result.agent_product_url or "N/A"),
                ("Tokens Removed", str(result.tracking_tokens_removed)),
                ("Short Domain", result.short_link_domain or "N/A"),
                ("Confidence", f"{result.confidence:.0%}"),
            ]

            for ridx, (label, value) in enumerate(fields):
                ctk.CTkLabel(
                    card,
                    text=f"{label}:",
                    font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_small"], weight="bold"),
                    anchor="w",
                ).grid(row=ridx, column=0, padx=10, pady=4, sticky="w")

                val_label = ctk.CTkLabel(
                    card,
                    text=value,
                    font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_small"]),
                    anchor="w",
                    wraplength=700,
                    cursor="hand2" if value.startswith("http") else None,
                    text_color=UI_THEME["primary_color"] if value.startswith("http") else UI_THEME["text_color"],
                )
                val_label.grid(row=ridx, column=1, padx=10, pady=4, sticky="w")
                if value.startswith("http"):
                    val_label.bind(
                        "<Button-1>",
                        lambda e, url=value: webbrowser.open(url),
                    )

    # -----------------------------------------------------------------------
    # Entry Point
    # -----------------------------------------------------------------------
    def run(self):
        """Run the application with error handling."""
        try:
            self.start()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received. Shutting down...")
        except Exception as exc:
            logger.critical("Fatal error: %s", exc, exc_info=True)
            traceback.print_exc()
        finally:
            self.shutdown()


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
def main():
    app = ApplicationController()
    app.run()


if __name__ == "__main__":
    main()
