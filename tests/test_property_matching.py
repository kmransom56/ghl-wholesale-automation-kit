"""Unit tests for property matching."""

import pytest

from src.workflows.property_matching import PropertyMatcher


class TestPropertyMatcher:
    @pytest.fixture
    def matcher(self) -> PropertyMatcher:
        return PropertyMatcher()

    @pytest.fixture
    def sample_property(self) -> dict:
        return {
            "after_repair_value": 300000,
            "repair_costs": 40000,
            "property_type": "Single Family",
            "market": "Dallas, TX",
        }

    @pytest.fixture
    def sample_investors(self) -> list[dict]:
        return [
            {
                "name": "Gold Investor",
                "cash_available": 500000,
                "min_property_price": 200000,
                "max_property_price": 400000,
                "preferred_property_types": ["Single Family", "Duplex"],
                "target_markets": ["Dallas, TX", "Houston, TX"],
            },
            {
                "name": "Silver Investor",
                "cash_available": 250000,
                "min_property_price": 150000,
                "max_property_price": 350000,
                "preferred_property_types": ["Single Family"],
                "target_markets": ["Austin, TX"],
            },
            {
                "name": "No Match Investor",
                "cash_available": 100000,
                "min_property_price": 500000,
                "max_property_price": 1000000,
                "preferred_property_types": ["Commercial"],
                "target_markets": ["New York, NY"],
            },
        ]

    def test_find_best_matches(
        self,
        matcher: PropertyMatcher,
        sample_property: dict,
        sample_investors: list[dict],
    ) -> None:
        matches = matcher.match_property_to_investors(sample_property, sample_investors)
        assert len(matches) > 0
        assert matches[0][0]["name"] == "Gold Investor"
        assert matches[0][1] > 75

    def test_price_match_scoring(
        self,
        matcher: PropertyMatcher,
        sample_property: dict,
        sample_investors: list[dict],
    ) -> None:
        score = matcher._score_price_match(
            sample_property["after_repair_value"], sample_investors[0]
        )
        assert score == 100

    def test_cash_sufficiency_scoring(
        self, matcher: PropertyMatcher, sample_property: dict
    ) -> None:
        investor_high_cash = {"cash_available": 500000}
        score = matcher._score_cash_match(
            investor_high_cash["cash_available"], sample_property
        )
        assert score == 100

    def test_no_matches_for_wrong_market(
        self,
        matcher: PropertyMatcher,
        sample_property: dict,
        sample_investors: list[dict],
    ) -> None:
        sample_property["market"] = "Los Angeles, CA"
        matches = matcher.match_property_to_investors(sample_property, sample_investors)
        for investor, score in matches:
            if investor["name"] == "No Match Investor":
                assert score < 50
