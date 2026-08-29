"""70% rule calculator: MAO = (ARV × rule%) − repair costs."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class SeventyPercentCalculator:
    def __init__(self, rule_pct: float | None = None, offer_multiplier: float | None = None):
        self.rule_pct = rule_pct or float(os.getenv("WHOLESALE_70_RULE_PERCENTAGE", "0.70"))
        self.offer_multiplier = offer_multiplier or float(
            os.getenv("WHOLESALE_OFFER_MULTIPLIER", "0.95")
        )

    def calculate_max_offer(self, property_data: dict[str, Any]) -> dict[str, float | bool]:
        arv = float(property_data.get("after_repair_value", 0) or 0)
        repair_costs = float(property_data.get("repair_costs", 0) or 0)
        asking_price = float(property_data.get("current_asking_price", 0) or 0)

        max_offer = (arv * self.rule_pct) - repair_costs
        profit_at_asking = arv - asking_price - repair_costs

        return {
            "arv": arv,
            "repair_costs": repair_costs,
            "asking_price": asking_price,
            "max_offer": max(0.0, max_offer),
            "offer_price": max(0.0, max_offer * self.offer_multiplier),
            "estimated_profit": max(0.0, profit_at_asking),
            "profit_margin_percent": (profit_at_asking / arv * 100) if arv > 0 else 0.0,
            "is_good_deal": profit_at_asking > 0 and profit_at_asking > (arv * 0.10),
        }

    def validate_repair_estimate(self, property_data: dict[str, Any]) -> dict[str, str]:
        arv = float(property_data.get("after_repair_value", 0) or 0)
        repair_costs = float(property_data.get("repair_costs", 0) or 0)
        if arv <= 0:
            return {"status": "warning", "message": "ARV missing for repair validation"}
        typical_min = arv * 0.10
        typical_max = arv * 0.30
        if repair_costs < typical_min:
            return {"status": "warning", "message": "Repair estimate seems low"}
        if repair_costs > typical_max:
            return {"status": "warning", "message": "Repair estimate seems high"}
        return {"status": "ok", "message": "Repair estimate in normal range"}
