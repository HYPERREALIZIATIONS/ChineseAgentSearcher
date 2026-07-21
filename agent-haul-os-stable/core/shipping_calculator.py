"""
core/shipping_calculator.py
Mathematical pricing engine that computes Actual vs Volumetric Weight
((L * W * H) / 5000 or / 6000) and evaluates base fees against additional
weight parameters across LitBuy, AllChinaBuy, Hoobuy, and Superbuy.
"""

import math
import threading
from typing import Dict, List, Optional, Tuple, Any

from config.settings import (
    SHIPPING_LINE_RULES,
    AGENT_MARKUP_RULES,
    SUPPORTED_DESTINATIONS,
    SUPPORTED_AGENTS,
)


# ---------------------------------------------------------------------------
# Weight Calculation
# ---------------------------------------------------------------------------
def calculate_volumetric_weight(length_cm: float, width_cm: float, height_cm: float, divisor: int = 5000) -> float:
    """
    Compute volumetric weight in kilograms.
    Formula: (L * W * H) / divisor
    Default divisor is 5000 for international express carriers.
    Some destinations (EU) use 6000 for economy lines.
    """
    if length_cm <= 0 or width_cm <= 0 or height_cm <= 0:
        raise ValueError("Package dimensions must be positive numbers.")
    if divisor <= 0:
        raise ValueError("Volumetric divisor must be positive.")
    volume_cubic_cm = length_cm * width_cm * height_cm
    volumetric_kg = volume_cubic_cm / float(divisor)
    return round(volumetric_kg, 4)


def calculate_chargeable_weight(
    actual_weight_kg: float,
    length_cm: float,
    width_cm: float,
    height_cm: float,
    divisor: int = 5000,
) -> float:
    """
    Return the greater of actual weight and volumetric weight.
    This is the standard chargeable weight rule used by most carriers.
    """
    if actual_weight_kg < 0:
        raise ValueError("Actual weight cannot be negative.")
    vol = calculate_volumetric_weight(length_cm, width_cm, height_cm, divisor)
    return max(actual_weight_kg, vol)


# ---------------------------------------------------------------------------
# Shipping Line Cost Calculator
# ---------------------------------------------------------------------------
class ShippingLineCost:
    """Holds the calculated cost breakdown for a single shipping line."""

    __slots__ = (
        "line_name",
        "base_fee",
        "per_kg_rate",
        "first_weight_kg",
        "additional_weight_kg",
        "fuel_surcharge_pct",
        "remote_area_fee",
        "volumetric_divisor",
        "actual_weight",
        "volumetric_weight",
        "chargeable_weight",
        "base_shipping_cost",
        "weight_surcharge",
        "fuel_surcharge",
        "remote_area_cost",
        "total_shipping_cost",
        "notes",
    )

    def __init__(
        self,
        line_name: str = "",
        base_fee: float = 0.0,
        per_kg_rate: float = 0.0,
        first_weight_kg: float = 0.5,
        additional_weight_kg: float = 0.5,
        fuel_surcharge_pct: float = 0.0,
        remote_area_fee: float = 0.0,
        volumetric_divisor: int = 5000,
        actual_weight: float = 0.0,
        volumetric_weight: float = 0.0,
        notes: str = "",
    ):
        self.line_name = line_name
        self.base_fee = base_fee
        self.per_kg_rate = per_kg_rate
        self.first_weight_kg = first_weight_kg
        self.additional_weight_kg = additional_weight_kg
        self.fuel_surcharge_pct = fuel_surcharge_pct
        self.remote_area_fee = remote_area_fee
        self.volumetric_divisor = volumetric_divisor
        self.actual_weight = actual_weight
        self.volumetric_weight = volumetric_weight
        self.chargeable_weight = 0.0
        self.base_shipping_cost = 0.0
        self.weight_surcharge = 0.0
        self.fuel_surcharge = 0.0
        self.remote_area_cost = 0.0
        self.total_shipping_cost = 0.0
        self.notes = notes

    def compute(self) -> None:
        """
        Run the full cost calculation and populate all fields.
        Carrier pricing model:
        - Base fee covers the first_weight_kg.
        - Additional weight is charged in blocks of additional_weight_kg.
        """
        self.chargeable_weight = max(self.actual_weight, self.volumetric_weight)

        # Base shipping cost
        self.base_shipping_cost = self.base_fee

        # Additional weight surcharge
        if self.chargeable_weight > self.first_weight_kg:
            excess = self.chargeable_weight - self.first_weight_kg
            blocks = math.ceil(excess / self.additional_weight_kg)
            self.weight_surcharge = blocks * self.additional_weight_kg * self.per_kg_rate
        else:
            self.weight_surcharge = 0.0

        # Fuel surcharge (applied to base + weight surcharge)
        subtotal = self.base_shipping_cost + self.weight_surcharge
        self.fuel_surcharge = round(subtotal * self.fuel_surcharge_pct, 2)

        # Remote area surcharge
        self.remote_area_cost = self.remote_area_fee if self.remote_area_fee > 0 else 0.0

        self.total_shipping_cost = round(
            self.base_shipping_cost
            + self.weight_surcharge
            + self.fuel_surcharge
            + self.remote_area_cost,
            2,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_name": self.line_name,
            "base_fee": self.base_fee,
            "per_kg_rate": self.per_kg_rate,
            "first_weight_kg": self.first_weight_kg,
            "additional_weight_kg": self.additional_weight_kg,
            "fuel_surcharge_pct": self.fuel_surcharge_pct,
            "remote_area_fee": self.remote_area_fee,
            "volumetric_divisor": self.volumetric_divisor,
            "actual_weight": self.actual_weight,
            "volumetric_weight": self.volumetric_weight,
            "chargeable_weight": self.chargeable_weight,
            "base_shipping_cost": self.base_shipping_cost,
            "weight_surcharge": self.weight_surcharge,
            "fuel_surcharge": self.fuel_surcharge,
            "remote_area_cost": self.remote_area_cost,
            "total_shipping_cost": self.total_shipping_cost,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Agent Landed Cost Calculator
# ---------------------------------------------------------------------------
class AgentLandedCost:
    """Holds the full landed cost breakdown for a single agent."""

    __slots__ = (
        "agent_name",
        "item_price_cny",
        "service_fee_pct",
        "handling_fee",
        "insurance_pct",
        "promo_discount_pct",
        "shipping_lines",
        "total_shipping_cost",
        "service_fee",
        "handling_cost",
        "insurance_cost",
        "promo_discount",
        "total_landed_cost",
        "selected_line_name",
    )

    def __init__(
        self,
        agent_name: str,
        item_price_cny: float,
        shipping_lines: Optional[List[ShippingLineCost]] = None,
        service_fee_pct: float = 0.0,
        handling_fee: float = 0.0,
        insurance_pct: float = 0.0,
        promo_discount_pct: float = 0.0,
    ):
        self.agent_name = agent_name
        self.item_price_cny = item_price_cny
        self.service_fee_pct = service_fee_pct
        self.handling_fee = handling_fee
        self.insurance_pct = insurance_pct
        self.promo_discount_pct = promo_discount_pct
        self.shipping_lines = shipping_lines or []
        self.total_shipping_cost = 0.0
        self.service_fee = 0.0
        self.handling_cost = 0.0
        self.insurance_cost = 0.0
        self.promo_discount = 0.0
        self.total_landed_cost = 0.0
        self.selected_line_name = ""

    def compute(self, selected_line_name: Optional[str] = None) -> None:
        """Calculate all cost components based on the selected shipping line."""
        if selected_line_name:
            self.selected_line_name = selected_line_name
        elif self.shipping_lines:
            # Default to the cheapest line
            self.selected_line_name = min(
                (line.line_name for line in self.shipping_lines),
                key=lambda name: next(
                    line.total_shipping_cost for line in self.shipping_lines if line.line_name == name
                ),
            )

        line_cost = next(
            (line for line in self.shipping_lines if line.line_name == self.selected_line_name),
            None,
        )
        if line_cost:
            self.total_shipping_cost = line_cost.total_shipping_cost
        else:
            self.total_shipping_cost = 0.0

        self.service_fee = round(self.item_price_cny * self.service_fee_pct, 2)
        self.handling_cost = self.handling_fee
        self.insurance_cost = round(self.item_price_cny * self.insurance_pct, 2)
        self.promo_discount = round(self.item_price_cny * self.promo_discount_pct, 2)

        self.total_landed_cost = round(
            self.item_price_cny
            + self.service_fee
            + self.handling_cost
            + self.insurance_cost
            - self.promo_discount
            + self.total_shipping_cost,
            2,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "item_price_cny": self.item_price_cny,
            "service_fee_pct": self.service_fee_pct,
            "handling_fee": self.handling_fee,
            "insurance_pct": self.insurance_pct,
            "promo_discount_pct": self.promo_discount_pct,
            "selected_line_name": self.selected_line_name,
            "total_shipping_cost": self.total_shipping_cost,
            "service_fee": self.service_fee,
            "handling_cost": self.handling_cost,
            "insurance_cost": self.insurance_cost,
            "promo_discount": self.promo_discount,
            "total_landed_cost": self.total_landed_cost,
        }


# ---------------------------------------------------------------------------
# Master Freight Calculator
# ---------------------------------------------------------------------------
class ShippingCalculator:
    """
    Thread-safe shipping calculator that evaluates all agents and all
    available shipping lines for a given package and destination.
    """

    def __init__(self):
        self._lock = threading.RLock()

    def calculate_all(
        self,
        actual_weight_kg: float,
        length_cm: float,
        width_cm: float,
        height_cm: float,
        destination: str,
        item_price_cny: float = 0.0,
        agent_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Compute and return a list of cost dictionaries for every agent
        and every shipping line available for the destination.
        """
        if destination not in SUPPORTED_DESTINATIONS:
            raise ValueError(
                f"Unsupported destination '{destination}'. "
                f"Supported: {', '.join(SUPPORTED_DESTINATIONS)}"
            )

        with self._lock:
            carrier_rules = SHIPPING_LINE_RULES.get(destination, {}).get("carriers", {})
            agents_to_calc = [agent_name] if agent_name and agent_name in SUPPORTED_AGENTS else list(SUPPORTED_AGENTS)

            results: List[Dict[str, Any]] = []

            for ag_name in agents_to_calc:
                markup = AGENT_MARKUP_RULES.get(ag_name, {})
                service_fee_pct = markup.get("service_fee_pct", 0.0)
                handling_fee = markup.get("handling_fee", 0.0)
                insurance_pct = markup.get("insurance_pct", 0.0)
                promo_discount_pct = markup.get("promo_discount_pct", 0.0)

                lines: List[ShippingLineCost] = []
                for line_name, line_rule in carrier_rules.items():
                    divisor = line_rule.get("volumetric_divisor", 5000)
                    vol_weight = calculate_volumetric_weight(
                        length_cm, width_cm, height_cm, divisor
                    )
                    chargeable = calculate_chargeable_weight(
                        actual_weight_kg, length_cm, width_cm, height_cm, divisor
                    )

                    line_cost = ShippingLineCost(
                        line_name=line_name,
                        base_fee=line_rule.get("base_fee", 0.0),
                        per_kg_rate=line_rule.get("per_kg_rate", 0.0),
                        first_weight_kg=line_rule.get("first_weight_kg", 0.5),
                        additional_weight_kg=line_rule.get("additional_weight_kg", 0.5),
                        fuel_surcharge_pct=line_rule.get("fuel_surcharge_pct", 0.0),
                        remote_area_fee=line_rule.get("remote_area_fee", 0.0),
                        volumetric_divisor=divisor,
                        actual_weight=actual_weight_kg,
                        volumetric_weight=vol_weight,
                        notes=line_rule.get("notes", ""),
                    )
                    line_cost.compute()
                    lines.append(line_cost)

                agent_cost = AgentLandedCost(
                    agent_name=ag_name,
                    item_price_cny=item_price_cny,
                    shipping_lines=lines,
                    service_fee_pct=service_fee_pct,
                    handling_fee=handling_fee,
                    insurance_pct=insurance_pct,
                    promo_discount_pct=promo_discount_pct,
                )
                agent_cost.compute()
                agent_dict = agent_cost.to_dict()

                # Attach line details and best cost for the UI matrix
                line_dicts = [line.to_dict() for line in lines]
                best_shipping = min(
                    (line["total_shipping_cost"] for line in line_dicts),
                    default=0.0,
                )
                agent_dict["shipping_lines"] = line_dicts
                agent_dict["best_shipping_cost"] = best_shipping
                agent_dict["chargeable_weight"] = lines[0].chargeable_weight if lines else 0.0

                results.append(agent_dict)

            return results

    def calculate_quick(
        self,
        actual_weight_kg: float,
        length_cm: float,
        width_cm: float,
        height_cm: float,
        destination: str,
    ) -> Dict[str, Any]:
        """
        Quick single-agent calculation (defaults to LitBuy).
        Returns a simplified dict with chargeable weight and cost.
        """
        results = self.calculate_all(
            actual_weight_kg=actual_weight_kg,
            length_cm=length_cm,
            width_cm=width_cm,
            height_cm=height_cm,
            destination=destination,
            item_price_cny=0.0,
            agent_name="litbuy",
        )
        if results:
            return results[0]
        return {}
