"""End-to-end wholesale deal workflow (GHL-native, no Zapier)."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv

from src.integrations.ghl_client import GHLClient
from src.workflows.seventy_percent_rule import SeventyPercentCalculator

load_dotenv()
logger = logging.getLogger(__name__)


class WholesaleAutomationSystem:
    def __init__(self, ghl: GHLClient | None = None) -> None:
        self.ghl = ghl or GHLClient()
        self.calculator = SeventyPercentCalculator()
        self.partner_driven_api_key = os.getenv("PARTNER_DRIVEN_API_KEY", "")
        self.partner_driven_url = os.getenv(
            "PARTNER_DRIVEN_BASE_URL", "https://api.partnerdriven.com"
        ).rstrip("/")
        self.fee_threshold = float(os.getenv("PARTNER_DRIVEN_FEE_THRESHOLD", "15000"))
        self.repair_threshold = float(os.getenv("PARTNER_DRIVEN_REPAIR_THRESHOLD", "30000"))
        self.pipeline_id = os.getenv("GHL_PIPELINE_ID", "")
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    def calculate_70_rule(self, arv: float, repairs: float) -> dict[str, Any]:
        result = self.calculator.calculate_max_offer(
            {"after_repair_value": arv, "repair_costs": repairs}
        )
        return {
            "arv": result["arv"],
            "repairs": result["repair_costs"],
            "mao": result["max_offer"],
            "offer_price": result["offer_price"],
            "investor_spread": max(0.0, float(result["max_offer"]) - float(result["offer_price"])),
            "calculation_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def create_ghl_contact(self, contact_data: dict[str, Any]) -> str | None:
        if self.dry_run:
            return "dry-run-contact-id"
        try:
            created = self.ghl.create_contact(
                name=f"{contact_data.get('owner_first_name', '')} {contact_data.get('owner_last_name', '')}".strip()
                or contact_data.get("owner_name", "Seller"),
                email=contact_data.get("owner_email", ""),
                phone=contact_data.get("owner_phone", ""),
                property_address=contact_data.get("property_address", ""),
                arv=contact_data.get("arv", ""),
                repairs=contact_data.get("repairs", ""),
                mao=contact_data.get("mao", ""),
                offer_price=contact_data.get("offer_price", ""),
                deal_source=contact_data.get("deal_source", "DealDriven"),
            )
            return created.get("id")
        except Exception as exc:
            logger.error("GHL contact creation failed: %s", exc)
            return None

    def create_opportunity(self, contact_id: str, deal_data: dict[str, Any]) -> str | None:
        if self.dry_run:
            return "dry-run-opportunity-id"
        try:
            result = self.ghl.create_opportunity(
                contact_id=contact_id,
                title=f"Wholesale Deal - {deal_data.get('property_address', 'Unknown')}",
                amount=float(deal_data.get("offer_price", 0) or 0),
                pipeline_id=self.pipeline_id,
            )
            return result.get("opportunity_id")
        except Exception as exc:
            logger.error("GHL opportunity creation failed: %s", exc)
            return None

    def route_deal_automatically(self, deal_data: dict[str, Any]) -> dict[str, Any]:
        assignment_fee = float(deal_data.get("investor_spread", 0) or 0)
        repair_estimate = float(deal_data.get("repairs", 0) or 0)
        routing = {
            "deal_id": deal_data.get("deal_id"),
            "assignment_fee": assignment_fee,
            "routing_decision": None,
            "reasoning": "",
        }
        if assignment_fee < self.fee_threshold or repair_estimate < self.repair_threshold:
            routing["routing_decision"] = "PARTNER_DRIVEN"
            routing["reasoning"] = (
                f"Assignment fee ${assignment_fee:,.0f} below ${self.fee_threshold:,.0f} "
                f"or repairs ${repair_estimate:,.0f} below ${self.repair_threshold:,.0f}"
            )
        else:
            routing["routing_decision"] = "DIRECT_INVESTOR"
            routing["reasoning"] = (
                f"Assignment fee ${assignment_fee:,.0f} meets direct-investor threshold"
            )
        return routing

    def submit_to_partner_driven(self, deal_data: dict[str, Any], contact_id: str) -> bool:
        if self.dry_run or not self.partner_driven_api_key:
            logger.info("Partner Driven submission skipped (dry_run or missing API key)")
            return False
        payload = {
            "property_address": deal_data.get("property_address"),
            "arv": deal_data.get("arv"),
            "repairs": deal_data.get("repairs"),
            "offer_price": deal_data.get("offer_price"),
            "seller_contact": {
                "name": deal_data.get("owner_name"),
                "phone": deal_data.get("owner_phone"),
                "email": deal_data.get("owner_email"),
            },
            "ghl_contact_id": contact_id,
            "deal_type": "Wholesale",
            "submission_type": "CONTRACT_AND_DEAL",
        }
        try:
            response = requests.post(
                f"{self.partner_driven_url}/deals/submit",
                headers={
                    "Authorization": f"Bearer {self.partner_driven_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            return response.status_code in (200, 201)
        except Exception as exc:
            logger.error("Partner Driven submission failed: %s", exc)
            return False

    def offer_post_close_services(
        self, contact_id: str, investor_data: dict[str, Any]
    ) -> dict[str, Any]:
        services: dict[str, Any] = {
            "contact_id": contact_id,
            "offered_services": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        services["offered_services"].append(
            {"service": "Credit Dawg", "monthly_fee": 49.00, "auto_enroll": True}
        )
        services["offered_services"].append(
            {"service": "Privacy Dawg", "monthly_fee": 19.99, "auto_enroll": True}
        )
        if investor_data.get("netintegrate_interest", False) and os.getenv(
            "NETINTEGRATE_AUTO_ENROLL", "false"
        ).lower() == "true":
            services["offered_services"].append(
                {
                    "service": "NetIntegrate",
                    "monthly_fee": "On-Demand",
                    "auto_enroll": False,
                    "note": "Offered based on investor need",
                }
            )
        return services

    def process_deal_workflow(self, deal_data: dict[str, Any]) -> dict[str, Any]:
        workflow_result: dict[str, Any] = {
            "workflow_id": f"DEAL_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "property_address": deal_data.get("property_address"),
            "steps_completed": [],
        }

        calculations = self.calculate_70_rule(
            float(deal_data.get("arv", 0) or 0),
            float(deal_data.get("repairs", 0) or 0),
        )
        deal_data.update(calculations)
        workflow_result["steps_completed"].append("70_rule_calculation")

        contact_id = self.create_ghl_contact(deal_data)
        if contact_id:
            deal_data["ghl_contact_id"] = contact_id
            workflow_result["steps_completed"].append("ghl_contact_created")

        if contact_id:
            opportunity_id = self.create_opportunity(contact_id, deal_data)
            if opportunity_id:
                deal_data["ghl_opportunity_id"] = opportunity_id
                workflow_result["steps_completed"].append("ghl_opportunity_created")

        routing = self.route_deal_automatically(deal_data)
        workflow_result["routing_decision"] = routing
        workflow_result["steps_completed"].append("deal_routing_decision")

        if routing["routing_decision"] == "PARTNER_DRIVEN" and contact_id:
            if self.submit_to_partner_driven(deal_data, contact_id):
                workflow_result["steps_completed"].append("partner_driven_submitted")

        if contact_id:
            services = self.offer_post_close_services(
                contact_id, deal_data.get("investor_data", {})
            )
            workflow_result["post_close_services"] = services
            workflow_result["steps_completed"].append("post_close_services_offered")

        workflow_result["status"] = "COMPLETED"
        workflow_result["timestamp"] = datetime.now(timezone.utc).isoformat()
        return workflow_result
