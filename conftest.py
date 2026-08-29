"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def test_env() -> None:
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("DRY_RUN", "true")
    os.environ.setdefault("GHL_API_KEY", "test_key")
    os.environ.setdefault("GHL_LOCATION_ID", "test_location")


@pytest.fixture
def sample_investor_data() -> dict:
    return {
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "555-1234",
        "cash_available": 500000,
        "deals_per_year": 8,
        "min_property_price": 100000,
        "max_property_price": 500000,
        "preferred_property_types": ["Single Family"],
        "target_markets": ["Dallas, TX"],
    }


@pytest.fixture
def sample_property_data() -> dict:
    return {
        "after_repair_value": 300000,
        "repair_costs": 40000,
        "current_asking_price": 160000,
        "property_type": "Single Family",
        "market": "Dallas, TX",
    }
