#!/usr/bin/env python3
"""GSCCCA property verification via Playwright web scraping."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

from playwright.async_api import Page, async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GSCCCAPropertyVerifier:
    """Verify Georgia property ownership records through GSCCCA search."""

    def __init__(self, base_url: str = "https://www.gsccca.org", timeout_ms: int = 30000):
        self.gsccca_url = base_url
        self.timeout = timeout_ms
        self.verification_results: list[dict[str, Any]] = []

    async def search_property(self, address: str, county: str) -> dict[str, Any] | None:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            try:
                await page.goto(self.gsccca_url, timeout=self.timeout)
                await page.wait_for_load_state("networkidle")

                search_link = page.locator('a:has-text("SEARCH")').first
                if await search_link.count():
                    await search_link.click(timeout=5000)
                    await page.wait_for_load_state("networkidle")

                address_field = page.locator('[name="address"]')
                if await address_field.count():
                    await address_field.fill(address, timeout=5000)

                county_field = page.locator('[name="county"]')
                if await county_field.count():
                    await county_field.select_option(county, timeout=5000)

                submit = page.locator('button:has-text("Search")').first
                if await submit.count():
                    await submit.click(timeout=5000)
                    await page.wait_for_load_state("networkidle")

                records = await self._extract_property_records(page)
                result = {
                    "address": address,
                    "county": county,
                    "search_timestamp": datetime.now(timezone.utc).isoformat(),
                    "records_found": len(records),
                    "records": records,
                }
                self.verification_results.append(result)
                return result
            except Exception as exc:
                logger.error("GSCCCA search failed for %s: %s", address, exc)
                return None
            finally:
                await context.close()
                await browser.close()

    async def _extract_property_records(self, page: Page) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        try:
            await page.wait_for_selector("table", timeout=10000)
            rows = await page.query_selector_all("table tbody tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) < 2:
                    continue
                values = [((await cell.text_content()) or "").strip() for cell in cells]
                records.append(
                    {
                        "owner": values[0] if values else "",
                        "parcel": values[1] if len(values) > 1 else "",
                        "details": values[2:] if len(values) > 2 else [],
                    }
                )
        except Exception as exc:
            logger.warning("Could not parse GSCCCA table: %s", exc)
        return records

    @staticmethod
    def parse_parcel_id(text: str) -> str:
        match = re.search(r"\d{6,}", text or "")
        return match.group(0) if match else ""

    def search_property_blocking(self, address: str, county: str) -> dict[str, Any] | None:
        return asyncio.run(self.search_property(address, county))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Verify property via GSCCCA")
    parser.add_argument("address", help="Street address")
    parser.add_argument("county", help="Georgia county name")
    args = parser.parse_args()

    verifier = GSCCCAPropertyVerifier()
    result = verifier.search_property_blocking(args.address, args.county)
    if result:
        print(f"Found {result['records_found']} record(s) for {args.address}")
    else:
        raise SystemExit("Verification failed")


if __name__ == "__main__":
    main()
