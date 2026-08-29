"""Unit tests for investor quality scoring."""

import pytest

from src.workflows.quality_scoring import InvestorScorer


class TestInvestorScorer:
    @pytest.fixture
    def scorer(self) -> InvestorScorer:
        return InvestorScorer()

    def test_calculate_quality_score_gold_investor(self, scorer: InvestorScorer) -> None:
        investor = {
            "cash_available": 750000,
            "deals_per_year": 12,
            "min_property_price": 100000,
            "max_property_price": 500000,
            "current_property_price": 300000,
        }
        score = scorer.calculate_quality_score(investor)
        assert score >= 80
        assert scorer.get_investor_tier(score) == "Gold"

    def test_calculate_quality_score_silver_investor(self, scorer: InvestorScorer) -> None:
        investor = {
            "cash_available": 350000,
            "deals_per_year": 3,
            "min_property_price": 150000,
            "max_property_price": 400000,
            "current_property_price": 250000,
        }
        score = scorer.calculate_quality_score(investor)
        assert 60 <= score < 80
        assert scorer.get_investor_tier(score) == "Silver"

    def test_calculate_quality_score_bronze_investor(self, scorer: InvestorScorer) -> None:
        investor = {
            "cash_available": 75000,
            "deals_per_year": 1,
            "min_property_price": 50000,
            "max_property_price": 200000,
            "current_property_price": 100000,
        }
        score = scorer.calculate_quality_score(investor)
        assert score < 60
        assert scorer.get_investor_tier(score) == "Bronze"

    def test_liquidity_scoring(self, scorer: InvestorScorer) -> None:
        assert scorer._calculate_liquidity_score({"cash_available": 500000}) == 100
        assert scorer._calculate_liquidity_score({"cash_available": 350000}) == 75
        assert scorer._calculate_liquidity_score({"cash_available": 150000}) == 50
        assert scorer._calculate_liquidity_score({"cash_available": 50000}) == 25

    def test_frequency_scoring(self, scorer: InvestorScorer) -> None:
        assert scorer._calculate_frequency_score({"deals_per_year": 12}) == 100
        assert scorer._calculate_frequency_score({"deals_per_year": 8}) == 75
        assert scorer._calculate_frequency_score({"deals_per_year": 3}) == 50
        assert scorer._calculate_frequency_score({"deals_per_year": 1}) == 25

    def test_score_bounds(self, scorer: InvestorScorer) -> None:
        extreme_high = {
            "cash_available": 10000000,
            "deals_per_year": 100,
            "min_property_price": 0,
            "max_property_price": 999999999,
            "current_property_price": 500000,
        }
        assert 0 <= scorer.calculate_quality_score(extreme_high) <= 100

        extreme_low = {
            "cash_available": 0,
            "deals_per_year": 0,
            "min_property_price": 1000000,
            "max_property_price": 2000000,
            "current_property_price": 100,
        }
        assert 0 <= scorer.calculate_quality_score(extreme_low) <= 100
