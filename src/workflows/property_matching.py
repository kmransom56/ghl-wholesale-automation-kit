"""Match wholesale properties to investor profiles."""

from __future__ import annotations

from typing import Any


class PropertyMatcher:
    def match_property_to_investors(
        self, property_data: dict[str, Any], investors: list[dict[str, Any]]
    ) -> list[tuple[dict[str, Any], int]]:
        matches: list[tuple[dict[str, Any], int]] = []
        for investor in investors:
            score = self._calculate_match_score(property_data, investor)
            if score > 0:
                matches.append((investor, score))
        return sorted(matches, key=lambda item: item[1], reverse=True)

    def _calculate_match_score(
        self, property_data: dict[str, Any], investor: dict[str, Any]
    ) -> int:
        price = float(property_data.get("after_repair_value", 0) or 0)
        price_match = self._score_price_match(price, investor)
        cash_match = self._score_cash_match(
            float(investor.get("cash_available", 0) or 0), property_data
        )
        type_match = self._score_type_match(property_data, investor)
        location_match = self._score_location_match(property_data, investor)
        score = int(
            (price_match * 0.35)
            + (cash_match * 0.30)
            + (type_match * 0.20)
            + (location_match * 0.15)
        )
        return min(max(score, 0), 100)

    def _score_price_match(self, property_price: float, investor: dict[str, Any]) -> int:
        min_price = float(investor.get("min_property_price", 0) or 0)
        max_price = float(investor.get("max_property_price", 9_999_999_999) or 0)
        if min_price <= property_price <= max_price:
            return 100
        if (min_price * 0.8) <= property_price <= (max_price * 1.2):
            return 75
        if (min_price * 0.5) <= property_price <= (max_price * 1.5):
            return 50
        return 0

    def _score_cash_match(
        self, investor_cash: float, property_data: dict[str, Any]
    ) -> int:
        arv = float(property_data.get("after_repair_value", 0) or 0)
        repairs = float(property_data.get("repair_costs", 0) or 0)
        total_needed = arv + repairs
        if investor_cash >= total_needed:
            return 100
        if investor_cash >= total_needed * 0.8:
            return 75
        if investor_cash >= total_needed * 0.5:
            return 50
        return 0

    def _score_type_match(
        self, property_data: dict[str, Any], investor: dict[str, Any]
    ) -> int:
        preferred = investor.get("preferred_property_types", []) or []
        prop_type = property_data.get("property_type", "")
        if not preferred:
            return 50
        return 100 if prop_type in preferred else 0

    def _score_location_match(
        self, property_data: dict[str, Any], investor: dict[str, Any]
    ) -> int:
        markets = investor.get("target_markets", []) or []
        market = property_data.get("market", "")
        if not markets:
            return 50
        return 100 if market in markets else 0
