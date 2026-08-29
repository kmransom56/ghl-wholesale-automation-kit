"""Integration tests for Flask webhook endpoints."""

import json

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


class TestWebhookEndpoints:
    def test_health_check(self, client) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"

    def test_calculate_score_success(self, client) -> None:
        payload = {
            "contactId": "test_contact_123",
            "cash_available": 500000,
            "deals_per_year": 10,
            "min_property_price": 100000,
            "max_property_price": 500000,
            "current_property_price": 300000,
        }
        response = client.post(
            "/api/webhooks/calculate-score",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["qualityScore"] >= 0
        assert data["tier"] in ["Gold", "Silver", "Bronze"]

    def test_calculate_score_missing_contact_id(self, client) -> None:
        payload = {"cash_available": 500000, "deals_per_year": 10}
        response = client.post(
            "/api/webhooks/calculate-score",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_seventy_percent_rule_success(self, client) -> None:
        payload = {
            "contactId": "test_contact_456",
            "after_repair_value": 250000,
            "repair_costs": 30000,
            "current_asking_price": 130000,
        }
        response = client.post(
            "/api/webhooks/seventy-percent-rule",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["max_offer"] > 0
        assert data["estimated_profit"] > 0

    def test_find_matches_success(self, client) -> None:
        payload = {
            "propertyPrice": 300000,
            "repair_costs": 40000,
            "minScore": 75,
            "location": "Dallas, TX",
            "investors": [
                {
                    "name": "Gold Investor",
                    "cash_available": 500000,
                    "min_property_price": 200000,
                    "max_property_price": 400000,
                    "preferred_property_types": ["Single Family"],
                    "target_markets": ["Dallas, TX"],
                }
            ],
        }
        response = client.post(
            "/api/webhooks/find-matches",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert len(data["matched_investors"]) >= 1
