"""
ui/freight_matrix.py
Responsive multi-agent comparative data grid component.
Renders a scrollable table comparing total landed cost across LitBuy,
AllChinaBuy, Hoobuy, and Superbuy for a given package and destination.
"""

import tkinter as tk
from typing import Dict, List, Optional, Any

import customtkinter as ctk

from config.settings import UI_THEME, SUPPORTED_AGENTS, SUPPORTED_DESTINATIONS
from ui.layout import DarkScrollableFrame


# ---------------------------------------------------------------------------
# Freight Matrix Widget
# ---------------------------------------------------------------------------
class FreightMatrix(ctk.CTkFrame):
    """
    Responsive multi-agent comparative data grid.
    Contains:
    - Dimension inputs (L, W, H) with sliders
    - Weight input with slider
    - Destination selector
    - Item price input in CNY
    - Comparative results grid showing per-agent landed cost breakdown
    """

    def __init__(
        self,
        master,
        on_calculate: Optional[callable] = None,
    ):
        super().__init__(master, fg_color="transparent")

        self.on_calculate = on_calculate
        self._results_data: Dict[str, Any] = {}

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Input panel
        input_frame = ctk.CTkFrame(self, corner_radius=8)
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(3, weight=1)
        input_frame.grid_columnconfigure(5, weight=1)

        # Dimensions
        ctk.CTkLabel(
            input_frame,
            text="Package Dimensions (cm):",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"], weight="bold"),
        ).grid(row=0, column=0, columnspan=6, padx=10, pady=(10, 5), sticky="w")

        self.length_var = tk.DoubleVar(value=30.0)
        self.width_var = tk.DoubleVar(value=20.0)
        self.height_var = tk.DoubleVar(value=10.0)

        self._add_dimension_row(input_frame, "Length", self.length_var, 0, 100, 1)
        self._add_dimension_row(input_frame, "Width", self.width_var, 2, 100, 3)
        self._add_dimension_row(input_frame, "Height", self.height_var, 4, 100, 5)

        # Weight
        row_idx = 1
        ctk.CTkLabel(
            input_frame,
            text="Weight (kg):",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
        ).grid(row=row_idx, column=0, padx=(10, 5), pady=10, sticky="w")

        self.weight_slider = ctk.CTkSlider(
            input_frame,
            from_=0.1,
            to=50.0,
            number_of_steps=500,
            variable=self.weight_var := tk.DoubleVar(value=1.0),
            command=lambda v: self._sync_weight_entry(),
        )
        self.weight_slider.grid(row=row_idx, column=1, padx=5, pady=10, sticky="ew")

        self.weight_entry = ctk.CTkEntry(input_frame, width=80, textvariable=self.weight_var)
        self.weight_entry.grid(row=row_idx, column=2, padx=5, pady=10, sticky="w")
        self.weight_entry.bind("<KeyRelease>", lambda e: self._sync_weight_slider())

        # Destination
        ctk.CTkLabel(
            input_frame,
            text="Destination:",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
        ).grid(row=row_idx, column=3, padx=(10, 5), pady=10, sticky="w")

        self.destination_option = ctk.CTkOptionMenu(
            input_frame,
            values=SUPPORTED_DESTINATIONS,
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
        )
        self.destination_option.grid(row=row_idx, column=4, padx=5, pady=10, sticky="w")
        self.destination_option.set("US")

        # Item price
        ctk.CTkLabel(
            input_frame,
            text="Item Price (CNY):",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
        ).grid(row=row_idx, column=5, padx=(10, 5), pady=10, sticky="w")

        self.item_price_entry = ctk.CTkEntry(input_frame, width=100, placeholder_text="0.00")
        self.item_price_entry.grid(row=row_idx, column=6, padx=5, pady=10, sticky="w")
        self.item_price_entry.insert(0, "0.00")

        # Calculate button
        self.calc_button = ctk.CTkButton(
            input_frame,
            text="Calculate Freight",
            command=self._trigger_calculate,
            fg_color=UI_THEME["primary_color"],
            hover_color=UI_THEME["secondary_color"],
            width=160,
        )
        self.calc_button.grid(row=1, column=7, padx=10, pady=10, sticky="e")

        # Results table
        results_frame = ctk.CTkFrame(self, corner_radius=8)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        self.table_scroll = DarkScrollableFrame(results_frame, label_text="Freight Comparison Matrix")
        self.table_scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.table_scroll.grid_columnconfigure(0, weight=1)

        self._empty_table_label = ctk.CTkLabel(
            self.table_scroll,
            text="Enter package details and click Calculate Freight.",
            text_color=UI_THEME["text_color_secondary"],
        )
        self._empty_table_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

    # -----------------------------------------------------------------------
    # Dimension Helpers
    # -----------------------------------------------------------------------
    def _add_dimension_row(self, parent, label_text, variable, col_idx, max_val, slider_col):
        ctk.CTkLabel(
            parent,
            text=f"{label_text} (cm):",
            font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
        ).grid(row=0, column=col_idx, padx=(10 if col_idx == 0 else 5, 5), pady=10, sticky="w")

        slider = ctk.CTkSlider(
            parent,
            from_=1.0,
            to=float(max_val),
            number_of_steps=999,
            variable=variable,
            command=lambda v, var=variable, ent=None: self._sync_entry_from_slider(var),
        )
        slider.grid(row=0, column=slider_col, padx=5, pady=10, sticky="ew")

        entry = ctk.CTkEntry(parent, width=70, textvariable=variable)
        entry.grid(row=0, column=slider_col + 1, padx=(5, 10), pady=10, sticky="w")
        entry.bind("<KeyRelease>", lambda e, var=variable, sld=slider: self._sync_slider_from_entry(var, sld))

    def _sync_entry_from_slider(self, variable):
        # Handled by textvariable binding; placeholder for future precision logic
        pass

    def _sync_slider_from_entry(self, variable, slider):
        try:
            val = float(variable.get())
            slider.set(val)
        except ValueError:
            pass

    def _sync_weight_entry(self):
        # textvariable handles sync; placeholder
        pass

    def _sync_weight_slider(self):
        try:
            val = float(self.weight_var.get())
            self.weight_slider.set(val)
        except ValueError:
            pass

    # -----------------------------------------------------------------------
    # Actions
    # -----------------------------------------------------------------------
    def _trigger_calculate(self):
        """Gather inputs and invoke the on_calculate callback."""
        if self.on_calculate is None:
            return
        try:
            length = float(self.length_var.get())
            width = float(self.width_var.get())
            height = float(self.height_var.get())
            weight = float(self.weight_var.get())
            destination = self.destination_option.get()
            item_price = float(self.item_price_entry.get().strip())
        except ValueError:
            return

        self.on_calculate(
            length_cm=length,
            width_cm=width,
            height_cm=height,
            weight_kg=weight,
            destination=destination,
            item_price_cny=item_price,
        )

    # -----------------------------------------------------------------------
    # Results Rendering
    # -----------------------------------------------------------------------
    def display_results(self, results: Dict[str, Any]):
        """Render the freight comparison matrix from computed results."""
        self._clear_table()
        if not results:
            self._empty_table_label.configure(text="No results to display.")
            self._empty_table_label.grid()
            return

        self._empty_table_label.grid_remove()

        # Header row
        header = ctk.CTkFrame(self.table_scroll, fg_color=UI_THEME["secondary_color"], corner_radius=4)
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=1)
        header.grid_columnconfigure(3, weight=1)
        header.grid_columnconfigure(4, weight=1)

        headers = ["Agent", "Shipping Line", "Chargeable Weight (kg)", "Shipping Cost (CNY)", "Total Landed (CNY)"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(
                header,
                text=text,
                font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"], weight="bold"),
                anchor="w",
            ).grid(row=0, column=col, padx=10, pady=8, sticky="w")

        # Data rows
        row_idx = 1
        for agent_name, agent_data in results.items():
            lines = agent_data.get("shipping_lines", [])
            for line in lines:
                row_frame = ctk.CTkFrame(self.table_scroll, fg_color=("gray90", "gray15"), corner_radius=4)
                row_frame.grid(row=row_idx, column=0, sticky="ew", padx=5, pady=2)
                row_frame.grid_columnconfigure(0, weight=0)
                row_frame.grid_columnconfigure(1, weight=1)
                row_frame.grid_columnconfigure(2, weight=1)
                row_frame.grid_columnconfigure(3, weight=1)
                row_frame.grid_columnconfigure(4, weight=1)

                is_best = line.get("total_shipping_cost") == agent_data.get("best_shipping_cost")
                text_color = UI_THEME["primary_color"] if is_best else UI_THEME["text_color"]
                weight_text = "DIM" if is_best and line.get("chargeable_weight") != agent_data.get("chargeable_weight") else f"{line.get('chargeable_weight', 0):.2f}"

                values = [
                    agent_name.upper(),
                    line.get("line_name", ""),
                    f"{line.get('chargeable_weight', 0):.2f}",
                    f"{line.get('total_shipping_cost', 0):.2f}",
                    f"{agent_data.get('total_landed_cost', 0):.2f}",
                ]

                for col, val in enumerate(values):
                    ctk.CTkLabel(
                        row_frame,
                        text=val,
                        font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_normal"]),
                        anchor="w",
                        text_color=text_color,
                    ).grid(row=0, column=col, padx=10, pady=6, sticky="w")

                row_idx += 1

        # Summary footer
        summary = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
        summary.grid(row=row_idx, column=0, sticky="ew", padx=5, pady=(10, 5))
        summary.grid_columnconfigure(0, weight=1)

        best_agent = min(
            ((agent, data.get("total_landed_cost", float("inf"))) for agent, data in results.items()),
            key=lambda x: x[1],
            default=(None, None),
        )
        if best_agent[0]:
            ctk.CTkLabel(
                summary,
                text=f"★ Best Landed Cost: {best_agent[0].upper()} — ¥{best_agent[1]:.2f} CNY total",
                font=ctk.CTkFont(family=UI_THEME["font_family"], size=UI_THEME["font_size_large"], weight="bold"),
                text_color=UI_THEME["primary_color"],
                anchor="w",
            ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

    def _clear_table(self):
        for widget in self.table_scroll.winfo_children():
            if widget != self._empty_table_label:
                widget.destroy()
        self._empty_table_label.configure(text="Enter package details and click Calculate Freight.")
        self._empty_table_label.grid()
