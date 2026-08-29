#!/usr/bin/env python3
"""Create required GHL custom fields for wholesale automation."""

import os

from dotenv import load_dotenv

from src.integrations.ghl_client import GHLClient

load_dotenv()


def main() -> None:
    if not os.getenv("GHL_API_KEY") or not os.getenv("GHL_LOCATION_ID"):
        raise SystemExit("Set GHL_API_KEY and GHL_LOCATION_ID in .env before running")

    client = GHLClient()
    fields = [
        (
            "Investor_Quality_Score",
            "NUMERICAL",
            "Investor quality score (0-100)",
        ),
        (
            "Investor_Tier",
            "SINGLE_OPTIONS",
            "Investor tier: Gold / Silver / Bronze",
        ),
        (
            "Property_Match_Score",
            "NUMERICAL",
            "Property match score for investor (0-100)",
        ),
    ]

    print("Creating GHL custom fields...")
    for name, field_type, description in fields:
        try:
            client.create_custom_field(name, field_type, description)
            print(f"  created: {name}")
        except Exception as exc:
            print(f"  skipped {name}: {exc}")
    print("Done.")


if __name__ == "__main__":
    main()
