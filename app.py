"""Flask webhook server for GHL wholesale automation."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from src.integrations.dealdriven_scraper import DealDrivenScraper
from src.integrations.ghl_client import GHLClient
from src.integrations.investor_sync import InvestorSync
from src.workflows.property_matching import PropertyMatcher
from src.workflows.quality_scoring import InvestorScorer
from src.workflows.seventy_percent_rule import SeventyPercentCalculator
from src.workflows.wholesale_automation import WholesaleAutomationSystem

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

ghl_client = GHLClient()
investor_scorer = InvestorScorer()
calculator = SeventyPercentCalculator()
matcher = PropertyMatcher()
automation = WholesaleAutomationSystem(ghl=ghl_client)


@app.get("/health")
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.1.0",
        }
    )


@app.post("/api/webhooks/calculate-score")
def calculate_quality_score():
    data = request.get_json(silent=True) or {}
    contact_id = data.get("contactId")
    if not contact_id:
        return jsonify({"error": "contactId required"}), 400
    investor_data = {
        "cash_available": float(data.get("cash_available", 0) or 0),
        "deals_per_year": int(data.get("deals_per_year", 0) or 0),
        "min_property_price": float(data.get("min_property_price", 0) or 0),
        "max_property_price": float(data.get("max_property_price", 9_999_999_999) or 0),
        "current_property_price": float(data.get("current_property_price", 0) or 0),
    }
    quality_score = investor_scorer.calculate_quality_score(investor_data)
    tier = investor_scorer.get_investor_tier(quality_score)
    return jsonify(
        {
            "success": True,
            "qualityScore": quality_score,
            "tier": tier,
            "contactId": contact_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.post("/api/webhooks/seventy-percent-rule")
def calculate_seventy_percent():
    data = request.get_json(silent=True) or {}
    property_data = {
        "after_repair_value": float(data.get("after_repair_value", 0) or 0),
        "repair_costs": float(data.get("repair_costs", 0) or 0),
        "current_asking_price": float(data.get("current_asking_price", 0) or 0),
    }
    result = calculator.calculate_max_offer(property_data)
    return jsonify(
        {
            "success": True,
            "arv": result["arv"],
            "repair_costs": result["repair_costs"],
            "max_offer": result["max_offer"],
            "offer_price": result["offer_price"],
            "estimated_profit": result["estimated_profit"],
            "profit_margin_percent": result["profit_margin_percent"],
            "is_good_deal": result["is_good_deal"],
            "contactId": data.get("contactId"),
        }
    )


@app.post("/api/webhooks/find-matches")
def find_matching_investors():
    data = request.get_json(silent=True) or {}
    property_data = {
        "after_repair_value": float(data.get("propertyPrice", 0) or 0),
        "repair_costs": float(data.get("repair_costs", 0) or 0),
        "market": data.get("location", ""),
        "property_type": data.get("property_type", "Single Family"),
    }
    min_score = int(data.get("minScore", 75) or 75)
    investors = data.get("investors", [])
    if not isinstance(investors, list):
        investors = []
    matches = matcher.match_property_to_investors(property_data, investors)
    filtered = [
        {"investor": inv, "match_score": score}
        for inv, score in matches
        if score >= min_score
    ]
    return jsonify(
        {
            "success": True,
            "matched_investors": filtered,
            "property_value": property_data["after_repair_value"],
            "min_score_filter": min_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.post("/api/webhooks/update-investor-stats")
def update_investor_stats():
    data = request.get_json(silent=True) or {}
    contact_id = data.get("contactId")
    if not contact_id:
        return jsonify({"error": "contactId required"}), 400
    try:
        contact = ghl_client.get_contact(contact_id)
        custom = contact.get("customFields", contact.get("customField", {}))
        if isinstance(custom, list):
            custom = {
                item.get("key", item.get("id", "")): item.get("value", item.get("field_value"))
                for item in custom
            }
        investor_data = {
            "cash_available": float(custom.get("cash_available", 0) or 0),
            "deals_per_year": int(custom.get("deals_per_year", 0) or 0),
            "min_property_price": float(custom.get("min_property_price", 0) or 0),
            "max_property_price": float(custom.get("max_property_price", 9_999_999_999) or 0),
        }
        quality_score = investor_scorer.calculate_quality_score(investor_data)
        tier = investor_scorer.get_investor_tier(quality_score)
        ghl_client.update_multiple_fields(
            contact_id,
            {
                "Investor_Quality_Score": quality_score,
                "Investor_Tier": tier,
            },
        )
        return jsonify(
            {
                "success": True,
                "contactId": contact_id,
                "updated_tier": tier,
                "updated_score": quality_score,
            }
        )
    except Exception as exc:
        logger.exception("update_investor_stats failed")
        return jsonify({"error": str(exc)}), 500


@app.post("/api/manual/sync-dealdriven")
def sync_dealdriven_investors():
    data = request.get_json(silent=True) or {}
    username = data.get("dealdriven_username") or os.getenv("DEALDRIVEN_USERNAME")
    password = data.get("dealdriven_password") or os.getenv("DEALDRIVEN_PASSWORD")
    if not username or not password:
        return jsonify({"error": "DealDriven credentials required"}), 400
    sync = InvestorSync(ghl=ghl_client, scraper=DealDrivenScraper(), scorer=investor_scorer)
    result = asyncio.run(sync.sync_from_dealdriven(username, password))
    return jsonify({"success": True, **result})


@app.post("/api/manual/process-deal")
def process_deal():
    data = request.get_json(silent=True) or {}
    if not data.get("property_address"):
        return jsonify({"error": "property_address required"}), 400
    result = automation.process_deal_workflow(data)
    return jsonify({"success": True, **result})


if __name__ == "__main__":
    port = int(os.getenv("SERVER_PORT", "5000"))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    logger.info("Starting GHL webhook server on port %s", port)
    app.run(host="0.0.0.0", port=port, debug=debug)
