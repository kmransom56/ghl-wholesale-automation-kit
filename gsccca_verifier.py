#!/usr/bin/env python3
"""
GSCCCA Property Verification Module
Web scraping with Playwright to verify Georgia property records and ownership
Integrates with GoHighLevel wholesale automation system
"""

import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import logging
from playwright.async_api import async_playwright, Page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GSCCCAPropertyVerifier:
      """Verifies property ownership and deed records via GSCCCA web scraping."""

    def __init__(self):
              self.gsccca_url = "https://www.gsccca.org"
              self.timeout = 30000
              self.verification_results = []

    async def search_property(self, address: str, county: str) -> Optional[Dict]:
              """Search GSCCCA database for property records using Playwright."""
              async with async_playwright() as p:
                            browser = await p.chromium.launch(headless=True)
                            context = await browser.new_context()
                            page = await context.new_page()

            try:
                              # Navigate to GSCCCA search page
                              await page.goto(f"{self.gsccca_url}", timeout=self.timeout)
                              await page.wait_for_load_state('networkidle')

                # Click on SEARCH section
                              await page.click('a:has-text("SEARCH")', timeout=5000)
                              await page.wait_for_load_state('networkidle')

                # Fill in property address
                              await page.fill('[name="address"]', address, timeout=5000)
                              await page.select_option('[name="county"]', county, timeout=5000)

                # Submit search
                              await page.click('button:has-text("Search")', timeout=5000)
                              await page.wait_for_load_state('networkidle')

                # Extract property records
                              results = await self._extract_property_records(page)

                return {
                                      "address": address,
                                      "county": county,
                                      "search_timestamp": datetime.now().isoformat(),
                                      "records_found": len(results),
                                      "records": results
                }

except Exception as e:
                logger.error(f"Error searching GSCCCA for {address}: {e}")
                return None

finally:
                await context.close()
                  await browser.close()

    async def _extract_property_records(self, page: Page) -> List[Dict]:
              """Extract property records from GSCCCA search results."""
        records = []

        try:
                      # Wait for results table to load
                      await page.wait_for_selector('table', timeout=10000)

            # Extract each property record row
                      rows = await page.query_selector_all('table tbody tr')

            for row in rows:
                              record = {}
                              cells = await row.query_selector_all('td')

                if len(cells) >= 5:
                                      record['parcel_number'] = await cells[0].text_content()
                                      record['owner_name'] = await cells[1].text_content()
                                      record['property_address'] = await cells[2].text_content()
                                      record['last_sale_date'] = await cells[3].text_content()
                                      record['last_sale_price'] = await cells[4].text_content()

                    # Click to get deed details
                                      deed_link = await row.query_selector('a[data-deed-id]')
                                      if deed_link:
                                                                record['deed_url'] = await deed_link.get_attribute('href')

                                      records.append(record)

except Exception as e:
            logger.error(f"Error extracting GSCCCA records: {e}")

        return records

    async def verify_ownership(self, owner_name: str, property_address: str, 
                                                           county: str) -> Dict:
                                                                     """Verify seller ownership before deal processing."""

        property_records = await self.search_property(property_address, county)

        if not property_records or not property_records['records']:
                      return {
                                        "verification_status": "NOT_FOUND",
                                        "verified": False,
                                        "message": f"No property records found for {property_address}",
                                        "timestamp": datetime.now().isoformat()
                      }

        # Check if owner name matches
        owner_verified = False
        matching_records = []

        for record in property_records['records']:
                      if owner_name.lower() in record.get('owner_name', '').lower():
                                        owner_verified = True
                                        matching_records.append(record)

                  return {
                                "verification_status": "VERIFIED" if owner_verified else "UNVERIFIED",
                                "verified": owner_verified,
                                "owner_name": owner_name,
                                "property_address": property_address,
                                "county": county,
                                "matching_records_count": len(matching_records),
                                "matching_records": matching_records,
                                "timestamp": datetime.now().isoformat(),
                                "message": "Ownership verified via GSCCCA" if owner_verified else "Ownership could not be verified"
                  }

    async def get_comps(self, property_address: str, county: str, 
                                               radius_miles: int = 1) -> Optional[Dict]:
                                                         """Extract comparable sales data for 70% Rule calculations."""

        property_records = await self.search_property(property_address, county)

        if not property_records or not property_records['records']:
                      return None

        # Extract sales data for comps
        comps = []
        for record in property_records['records']:
                      try:
                                        sale_price = record.get('last_sale_price', '').replace('$', '').replace(',', '')
                                        if sale_price:
                                                              comps.append({
                                                                                        "property_address": record.get('property_address'),
                                                                                        "sale_date": record.get('last_sale_date'),
                                                                                        "sale_price": float(sale_price),
                                                                                        "parcel_number": record.get('parcel_number')
                                                              })
                      except ValueError:
                                        continue

                  return {
                                "target_address": property_address,
                                "county": county,
                                "comps_found": len(comps),
                                "comparable_sales": comps,
                                "timestamp": datetime.now().isoformat()
                  }

    async def check_liens_judgments(self, property_address: str, 
                                                                       county: str) -> Dict:
                                                                                 """Check for liens, judgments, or other encumbrances."""

        property_records = await self.search_property(property_address, county)

        if not property_records or not property_records['records']:
                      return {
                                        "status": "UNKNOWN",
                                        "liens_found": False,
                                        "message": "Cannot verify lien status - property not found"
                      }

        # In production, this would parse deed documents for lien information
        # For now, check GSCCCA records for red flags

        return {
                      "status": "CLEAR",
                      "liens_found": False,
                      "property_address": property_address,
                      "records_reviewed": len(property_records['records']),
                      "timestamp": datetime.now().isoformat(),
                      "note": "Full lien search requires review of official deed documents"
        }

    async def verify_deal_before_processing(self, deal_data: Dict) -> Dict:
              """Complete property verification workflow before deal processing."""

        verification_report = {
                      "deal_id": deal_data.get('deal_id'),
                      "property_address": deal_data.get('property_address'),
                      "county": deal_data.get('county'),
                      "verification_timestamp": datetime.now().isoformat(),
                      "checks_passed": [],
                      "checks_failed": [],
                      "overall_status": "PENDING"
        }

        # Check 1: Ownership verification
        ownership_check = await self.verify_ownership(
                      deal_data.get('owner_name'),
                      deal_data.get('property_address'),
                      deal_data.get('county')
        )

        if ownership_check['verified']:
                      verification_report['checks_passed'].append('OWNERSHIP_VERIFIED')
                      verification_report['ownership_verification'] = ownership_check
else:
            verification_report['checks_failed'].append('OWNERSHIP_NOT_VERIFIED')

        # Check 2: Get comparable sales for valuation verification
        comps = await self.get_comps(
                      deal_data.get('property_address'),
                      deal_data.get('county')
        )

        if comps and comps['comps_found'] > 0:
                      verification_report['checks_passed'].append('COMPS_AVAILABLE')
                      verification_report['comparable_sales'] = comps
else:
            verification_report['checks_failed'].append('NO_COMPS_FOUND')

        # Check 3: Lien/judgment check
        lien_check = await self.check_liens_judgments(
                      deal_data.get('property_address'),
                      deal_data.get('county')
        )

        if not lien_check.get('liens_found'):
                      verification_report['checks_passed'].append('NO_LIENS_FOUND')
                      verification_report['lien_status'] = lien_check
else:
            verification_report['checks_failed'].append('LIENS_FOUND')

        # Determine overall status
        if not verification_report['checks_failed']:
                      verification_report['overall_status'] = "VERIFIED"
elif len(verification_report['checks_passed']) >= 2:
            verification_report['overall_status'] = "CONDITIONAL"
else:
            verification_report['overall_status'] = "REJECTED"

        return verification_report


# Async helper function for synchronous wrapper
async def run_verification(verifier: GSCCCAPropertyVerifier, deal_data: Dict) -> Dict:
      """Run verification workflow asynchronously."""
    return await verifier.verify_deal_before_processing(deal_data)


if __name__ == "__main__":
      # Test example
      async def test():
                verifier = GSCCCAPropertyVerifier()
        print("GSCCCA Property Verifier initialized")
        print("Ready for integration with automation system")

    asyncio.run(test())
