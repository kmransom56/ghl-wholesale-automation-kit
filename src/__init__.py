"""
GHL Wholesale Automation Package
"""

version = "1.0.0"
author = "GHL Wholesale Automation Team"

from src.integrations.ghl_client import GHLClient
from src.workflows.quality_scoring import InvestorScorer
from src.workflows.seventy_percent_rule import SeventyPercentCalculator
from src.workflows.property_matching import PropertyMatcher

__all__ = [
    "GHLClient",
        "InvestorScorer",
            "SeventyPercentCalculator",
                "PropertyMatcher"
                ]
