#!/usr/bin/env python3
"""
GHL Wholesale Automation - Automated Deployment & Partner Driven Integration
Context Engineering Kit for AI-powered wholesale real estate automation
"""

import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class WholesaleAutomationSystem:
      """Main automation system with Partner Driven integration and auto-deployment."""

    def __init__(self):
              self.ghl_api_key = os.getenv("GHL_API_KEY")
              self.ghl_location_id = os.getenv("GHL_LOCATION_ID")
              self.partner_driven_api_key = os.getenv("PARTNER_DRIVEN_API_KEY")
              self.ghl_base_url = "https://services.leadconnectorhq.com"
              self.partner_driven_url = "https://api.partnerdriven.com"

    def calculate_70_rule(self, arv: float, repairs: float) -> Dict:
              """Calculate MAO and offer price using 70% Rule.

                              Formula: MAO = (ARV * 0.70) - Repair_Costs
                                      Assignment_Fee = Investor_Price - Seller_Price (your profit)
                                              """
              mao = (arv * 0.70) - repairs
              offer_price = mao * 0.95

        return {
                      "arv": arv,
                      "repairs": repairs,
                      "mao": mao,
                      "offer_price": round(offer_price, 2),
                      "investor_spread": round(mao * 0.05, 2),
                      "calculation_timestamp": datetime.now().isoformat()
        }

    def create_ghl_contact(self, contact_data: Dict) -> Optional[str]:
              """Create contact in GoHighLevel with property and deal details."""
              try:
                            headers = {
                                              "Authorization": f"Bearer {self.ghl_api_key}",
                                              "Content-Type": "application/json"
                            }

            payload = {
                              "firstName": contact_data.get("owner_first_name", "Seller"),
                              "lastName": contact_data.get("owner_last_name", ""),
                              "email": contact_data.get("owner_email", ""),
                              "phone": contact_data.get("owner_phone", ""),
                              "address": contact_data.get("property_address", ""),
                              "customFields": {
                                                    "property_address": contact_data.get("property_address"),
                                                    "arv": contact_data.get("arv"),
                                                    "repairs": contact_data.get("repairs"),
                                                    "mao": contact_data.get("mao"),
                                                    "offer_price": contact_data.get("offer_price"),
                                                    "motivation_score": contact_data.get("motivation_score", 0),
                                                    "deal_source": "DealDriven"
                              }
            }

            response = requests.post(
                              f"{self.ghl_base_url}/v1/contacts/",
                              headers=headers,
                              json=payload,
                              timeout=10
            )

            if response.status_code == 201:
                              contact_id = response.json().get("id")
                              return contact_id
else:
                  print(f"GHL Contact creation failed: {response.status_code}")
                  return None

except Exception as e:
            print(f"Error creating GHL contact: {e}")
            return None

    def create_opportunity(self, contact_id: str, deal_data: Dict) -> Optional[str]:
              """Create deal opportunity in GHL."""
              try:
                            headers = {
                                              "Authorization": f"Bearer {self.ghl_api_key}",
                                              "Content-Type": "application/json"
                            }

            payload = {
                              "title": f"Wholesale Deal - {deal_data['property_address']}",
                              "contactId": contact_id,
                              "pipelineId": os.getenv("GHL_PIPELINE_ID"),
                              "status": "New Lead",
                              "value": deal_data.get("offer_price", 0),
                              "customFields": {
                                                    "assignment_fee": deal_data.get("investor_spread", 0),
                                                    "repair_estimate": deal_data.get("repairs", 0),
                                                    "property_address": deal_data.get("property_address"),
                                                    "deal_type": "Wholesale"
                              }
            }

            response = requests.post(
                              f"{self.ghl_base_url}/v1/opportunities/",
                              headers=headers,
                              json=payload,
                              timeout=10
            )

            if response.status_code == 201:
                              opportunity_id = response.json().get("id")
                              return opportunity_id
                          return None

except Exception as e:
            print(f"Error creating opportunity: {e}")
            return None

    def route_deal_automatically(self, deal_data: Dict) -> Dict:
              """Smart deal routing: Partner Driven (<$15K fee) vs Direct Investor (>$15K)."""
              assignment_fee = deal_data.get("investor_spread", 0)
              repair_estimate = deal_data.get("repairs", 0)

        routing = {
                      "deal_id": deal_data.get("deal_id"),
                      "assignment_fee": assignment_fee,
                      "routing_decision": None,
                      "reasoning": ""
        }

        if assignment_fee < 15000 or repair_estimate < 30000:
                      routing["routing_decision"] = "PARTNER_DRIVEN"
                      routing["reasoning"] = f"Assignment fee ${assignment_fee} < $15K threshold"
else:
              routing["routing_decision"] = "DIRECT_INVESTOR"
              routing["reasoning"] = f"Assignment fee ${assignment_fee} >= $15K - high-value deal"

        return routing

    def submit_to_partner_driven(self, deal_data: Dict, contact_id: str) -> bool:
              """Submit qualified deals to Partner Driven for contract & deal submission."""
              try:
                            headers = {
                                              "Authorization": f"Bearer {self.partner_driven_api_key}",
                                              "Content-Type": "application/json"
                            }

            payload = {
                              "property_address": deal_data.get("property_address"),
                              "arv": deal_data.get("arv"),
                              "repairs": deal_data.get("repairs"),
                              "offer_price": deal_data.get("offer_price"),
                              "seller_contact": {
                                                    "name": deal_data.get("owner_name"),
                                                    "phone": deal_data.get("owner_phone"),
                                                    "email": deal_data.get("owner_email")
                              },
                              "ghl_contact_id": contact_id,
                              "deal_type": "Wholesale",
                              "submission_type": "CONTRACT_AND_DEAL"
            }

            response = requests.post(
                              f"{self.partner_driven_url}/deals/submit",
                              headers=headers,
                              json=payload,
                              timeout=10
            )

            return response.status_code == 200

except Exception as e:
            print(f"Error submitting to Partner Driven: {e}")
            return False

    def offer_post_close_services(self, contact_id: str, investor_data: Dict) -> Dict:
              """Auto-offer post-close services: Credit Dawg, Privacy Dawg (conditional: NetIntegrate)."""
              services = {
                  "contact_id": contact_id,
                  "offered_services": [],
                  "timestamp": datetime.now().isoformat()
              }

        # Always offer these
              services["offered_services"].append({
                            "service": "Credit Dawg",
                            "monthly_fee": 49.00,
                            "auto_enroll": True
              })
        services["offered_services"].append({
                      "service": "Privacy Dawg",
                      "monthly_fee": 19.99,
                      "auto_enroll": True
        })

        # Conditional: Only offer if investor expresses need
        if investor_data.get("netintegrate_interest", False):
                      services["offered_services"].append({
                                        "service": "NetIntegrate",
                                        "monthly_fee": "On-Demand",
                                        "auto_enroll": False,
                                        "note": "Offered based on investor need"
                      })

        return services

    def process_deal_workflow(self, deal_data: Dict) -> Dict:
              """Complete end-to-end deal processing workflow."""
              workflow_result = {
                  "workflow_id": f"DEAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                  "property_address": deal_data.get("property_address"),
                  "steps_completed": []
              }

        # Step 1: Calculate deal metrics
              calculations = self.calculate_70_rule(
                            deal_data.get("arv", 0),
                            deal_data.get("repairs", 0)
              )
        deal_data.update(calculations)
        workflow_result["steps_completed"].append("70_rule_calculation")

        # Step 2: Create GHL contact
        contact_id = self.create_ghl_contact(deal_data)
        if contact_id:
                      deal_data["ghl_contact_id"] = contact_id
                      workflow_result["steps_completed"].append("ghl_contact_created")

        # Step 3: Create opportunity
        if contact_id:
                      opportunity_id = self.create_opportunity(contact_id, deal_data)
                      if opportunity_id:
                                        deal_data["ghl_opportunity_id"] = opportunity_id
                                        workflow_result["steps_completed"].append("ghl_opportunity_created")

                  # Step 4: Smart routing
                  routing = self.route_deal_automatically(deal_data)
        workflow_result["routing_decision"] = routing
        workflow_result["steps_completed"].append("deal_routing_decision")

        # Step 5: Submit to Partner Driven if applicable
        if routing["routing_decision"] == "PARTNER_DRIVEN" and contact_id:
                      success = self.submit_to_partner_driven(deal_data, contact_id)
                      if success:
                                        workflow_result["steps_completed"].append("partner_driven_submitted")

                  # Step 6: Offer post-close services
                  if contact_id:
                                services = self.offer_post_close_services(contact_id, deal_data.get("investor_data", {}))
                                workflow_result["post_close_services"] = services
                                workflow_result["steps_completed"].append("post_close_services_offered")

        workflow_result["status"] = "COMPLETED"
        workflow_result["timestamp"] = datetime.now().isoformat()

        return workflow_result


if __name__ == "__main__":
      system = WholesaleAutomationSystem()
      print("GHL Wholesale Automation System initialized")
      print("Ready for AI agent integration and task execution")
