"""Sync scored investors from DealDriven into GHL custom fields."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.integrations.dealdriven_scraper import DealDrivenScraper
from src.integrations.ghl_client import GHLClient
from src.workflows.quality_scoring import InvestorScorer

logger = logging.getLogger(__name__)


class InvestorSync:
    def __init__(
        self,
        ghl: GHLClient | None = None,
        scraper: DealDrivenScraper | None = None,
        scorer: InvestorScorer | None = None,
    ) -> None:
        self.ghl = ghl or GHLClient()
        self.scraper = scraper or DealDrivenScraper()
        self.scorer = scorer or InvestorScorer()

    async def sync_from_dealdriven(
        self, username: str, password: str
    ) -> dict[str, Any]:
        investors = await self.scraper.get_investors(username, password)
        created = 0
        updated = 0
        for investor in investors:
            quality_score = self.scorer.calculate_quality_score(investor)
            tier = self.scorer.get_investor_tier(quality_score)
            try:
                contact = self.ghl.create_contact(
                    name=investor.get("name", ""),
                    email=investor.get("email", ""),
                    phone=investor.get("phone", ""),
                )
                contact_id = contact.get("id")
                if not contact_id:
                    continue
                self.ghl.update_multiple_fields(
                    contact_id,
                    {
                        "Investor_Quality_Score": quality_score,
                        "Investor_Tier": tier,
                    },
                )
                created += 1
            except Exception as exc:
                logger.warning("Failed to sync investor %s: %s", investor.get("name"), exc)
                updated += 1
        return {
            "total_investors": len(investors),
            "ghl": {"created": created, "updated": updated},
            "status": "success" if investors else "empty",
        }

    def sync_from_dealdriven_blocking(
        self, username: str, password: str
    ) -> dict[str, Any]:
        return asyncio.run(self.sync_from_dealdriven(username, password))
