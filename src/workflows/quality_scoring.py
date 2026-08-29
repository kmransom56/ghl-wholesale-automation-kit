"""Investor quality scoring (0-100) and tier classification."""

from __future__ import annotations

from typing import Any


class InvestorScorer:
    """Quality = 35% liquidity + 35% frequency + 30% deal-size fit."""

    def calculate_quality_score(self, investor_data: dict[str, Any]) -> int:
        liquidity = self._calculate_liquidity_score(investor_data)
        frequency = self._calculate_frequency_score(investor_data)
        deal_size = self._calculate_deal_size_score(investor_data)
        score = int((liquidity * 0.35) + (frequency * 0.35) + (deal_size * 0.30))
        return min(max(score, 0), 100)

    def get_investor_tier(self, quality_score: int) -> str:
        if quality_score >= 80:
            return "Gold"
        if quality_score >= 60:
            return "Silver"
        return "Bronze"

    def _calculate_liquidity_score(self, investor_data: dict[str, Any]) -> int:
        cash_available = float(investor_data.get("cash_available", 0) or 0)
        if cash_available >= 500_000:
            return 100
        if cash_available >= 250_000:
            return 75
        if cash_available >= 100_000:
            return 50
        return 25

    def _calculate_frequency_score(self, investor_data: dict[str, Any]) -> int:
        deals_per_year = int(investor_data.get("deals_per_year", 0) or 0)
        if deals_per_year >= 12:
            return 100
        if deals_per_year >= 6:
            return 75
        if deals_per_year >= 2:
            return 50
        return 25

    def _calculate_deal_size_score(self, investor_data: dict[str, Any]) -> int:
        min_price = float(investor_data.get("min_property_price", 0) or 0)
        max_price = float(investor_data.get("max_property_price", 9_999_999_999) or 0)
        property_price = float(investor_data.get("current_property_price", 0) or 0)
        if min_price <= property_price <= max_price:
            return 100
        width = max(max_price - min_price, 1)
        if (min_price - width * 0.2) <= property_price <= (max_price + width * 0.2):
            return 75
        if (min_price - width * 0.5) <= property_price <= (max_price + width * 0.5):
            return 50
        return 25
