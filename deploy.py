#!/usr/bin/env python3
"""CLI entrypoint for wholesale automation workflows."""

from src.workflows.wholesale_automation import WholesaleAutomationSystem


def main() -> None:
    system = WholesaleAutomationSystem()
    print("GHL Wholesale Automation System initialized")
    print("Webhook server: python app.py")
    print("Custom fields:  python ghl_custom_fields.py")


if __name__ == "__main__":
    main()
