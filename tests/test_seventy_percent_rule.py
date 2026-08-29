"""Unit tests for 70% rule calculations."""

import pytest

from src.workflows.seventy_percent_rule import SeventyPercentCalculator


class TestSeventyPercentRule:
    @pytest.fixture
    def calculator(self) -> SeventyPercentCalculator:
        return SeventyPercentCalculator()

    def test_good_deal_calculation(self, calculator: SeventyPercentCalculator) -> None:
        property_data = {
            "after_repair_value": 250000,
            "repair_costs": 30000,
            "current_asking_price": 130000,
        }
        result = calculator.calculate_max_offer(property_data)
        assert result["arv"] == 250000
        assert result["repair_costs"] == 30000
        assert result["max_offer"] == (250000 * 0.70) - 30000
        assert result["is_good_deal"] is True
        assert result["estimated_profit"] > 0

    def test_bad_deal_calculation(self, calculator: SeventyPercentCalculator) -> None:
        property_data = {
            "after_repair_value": 200000,
            "repair_costs": 80000,
            "current_asking_price": 150000,
        }
        result = calculator.calculate_max_offer(property_data)
        assert result["is_good_deal"] is False

    def test_max_offer_never_negative(self, calculator: SeventyPercentCalculator) -> None:
        property_data = {
            "after_repair_value": 100000,
            "repair_costs": 100000,
            "current_asking_price": 50000,
        }
        result = calculator.calculate_max_offer(property_data)
        assert result["max_offer"] >= 0

    def test_repair_estimate_validation(self, calculator: SeventyPercentCalculator) -> None:
        property_data = {
            "after_repair_value": 300000,
            "repair_costs": 20000,
        }
        validation = calculator.validate_repair_estimate(property_data)
        assert validation["status"] == "warning"
        assert "low" in validation["message"].lower()

    def test_high_repair_estimate_warning(self, calculator: SeventyPercentCalculator) -> None:
        property_data = {
            "after_repair_value": 300000,
            "repair_costs": 120000,
        }
        validation = calculator.validate_repair_estimate(property_data)
        assert validation["status"] == "warning"
        assert "high" in validation["message"].lower()

    def test_normal_repair_estimate(self, calculator: SeventyPercentCalculator) -> None:
        property_data = {
            "after_repair_value": 300000,
            "repair_costs": 75000,
        }
        validation = calculator.validate_repair_estimate(property_data)
        assert validation["status"] == "ok"
