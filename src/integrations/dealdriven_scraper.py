"""DealDriven investor scraper (Playwright — no API key required)."""

from __future__ import annotations

import logging
import re
from typing import Any

from playwright.async_api import Page, async_playwright

logger = logging.getLogger(__name__)


class DealDrivenScraper:
    def __init__(self, base_url: str = "https://app.dealdriven.com", timeout_ms: int = 30_000):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_ms

    async def get_investors(self, username: str, password: str) -> list[dict[str, Any]]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            try:
                await self._login(page, username, password)
                await page.goto(f"{self.base_url}/investors", wait_until="networkidle")
                investors = await self._scrape_investors_list(page)
                logger.info("Scraped %s investors from DealDriven", len(investors))
                return investors
            finally:
                await context.close()
                await browser.close()

    async def _login(self, page: Page, username: str, password: str) -> None:
        await page.goto(f"{self.base_url}/login", wait_until="networkidle")
        await page.fill('input[name="email"], input[type="email"]', username)
        await page.fill('input[name="password"], input[type="password"]', password)
        await page.click('button:has-text("Sign In"), button[type="submit"]')
        await page.wait_for_load_state("networkidle", timeout=self.timeout)

    async def _scrape_investors_list(self, page: Page) -> list[dict[str, Any]]:
        investors: list[dict[str, Any]] = []
        if not await page.query_selector("table tbody tr"):
            logger.warning("DealDriven investors table not found — selectors may have changed")
            return investors

        rows = await page.query_selector_all("table tbody tr")
        for row in rows:
            cells = await row.query_selector_all("td")
            if len(cells) < 3:
                continue
            name = (await cells[0].text_content() or "").strip()
            email = (await cells[1].text_content() or "").strip() if len(cells) > 1 else ""
            phone = (await cells[2].text_content() or "").strip() if len(cells) > 2 else ""
            cash_text = (await cells[3].text_content() or "").strip() if len(cells) > 3 else ""
            deals_text = (await cells[4].text_content() or "").strip() if len(cells) > 4 else ""
            if not name:
                continue
            investors.append(
                {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "cash_available": self._parse_currency(cash_text),
                    "deals_per_year": self._parse_number(deals_text),
                    "min_property_price": 0,
                    "max_property_price": 9_999_999_999,
                    "preferred_property_types": [],
                    "target_markets": [],
                    "status": "active",
                }
            )
        return investors

    @staticmethod
    def _parse_currency(value: str) -> float:
        cleaned = value.replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_number(value: str) -> int:
        match = re.search(r"\d+", value or "")
        return int(match.group()) if match else 0
