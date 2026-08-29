"""GoHighLevel API client (Lead Connector / services.leadconnectorhq.com)."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GHLClient:
    """Sync GHL client for contacts, custom fields, opportunities, and workflows."""

    def __init__(
        self,
        api_key: str | None = None,
        location_id: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("GHL_API_KEY", "")
        self.location_id = location_id or os.getenv("GHL_LOCATION_ID", "")
        self.base_url = (
            base_url
            or os.getenv("GHL_BASE_URL", "https://services.leadconnectorhq.com")
        ).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Version": "2021-07-28",
            }
        )

    def _request(
        self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        response = self.session.request(method, url, timeout=30, **kwargs)
        return response

    @staticmethod
    def _field_key(name: str) -> str:
        key = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
        return key.strip("_")

    def create_custom_field(
        self, field_name: str, field_type: str, description: str = ""
    ) -> dict[str, Any]:
        payload = {
            "name": field_name,
            "dataType": field_type,
            "description": description,
        }
        response = self._request(
            "POST",
            f"/locations/{self.location_id}/customFields",
            json=payload,
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"create_custom_field failed ({response.status_code}): {response.text}"
            )
        return response.json()

    def get_custom_fields(self) -> list[dict[str, Any]]:
        response = self._request(
            "GET", f"/locations/{self.location_id}/customFields"
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"get_custom_fields failed ({response.status_code}): {response.text}"
            )
        data = response.json()
        return data.get("customFields", data.get("fields", []))

    def create_contact(
        self,
        name: str = "",
        email: str = "",
        phone: str = "",
        **custom_fields: Any,
    ) -> dict[str, Any]:
        parts = name.split(maxsplit=1)
        payload: dict[str, Any] = {
            "locationId": self.location_id,
            "firstName": parts[0] if parts else "",
            "lastName": parts[1] if len(parts) > 1 else "",
            "email": email,
            "phone": phone,
        }
        if custom_fields:
            payload["customFields"] = [
                {"key": self._field_key(k), "field_value": str(v)}
                for k, v in custom_fields.items()
            ]
        response = self._request("POST", "/contacts/", json=payload)
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"create_contact failed ({response.status_code}): {response.text}"
            )
        body = response.json()
        contact = body.get("contact", body)
        return {"id": contact.get("id"), "name": name, "raw": contact}

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        response = self._request("GET", f"/contacts/{contact_id}")
        if response.status_code != 200:
            raise RuntimeError(
                f"get_contact failed ({response.status_code}): {response.text}"
            )
        body = response.json()
        return body.get("contact", body)

    def update_contact_field(
        self, contact_id: str, field_name: str, value: Any
    ) -> dict[str, Any]:
        payload = {
            "customFields": [
                {"key": self._field_key(field_name), "field_value": str(value)}
            ]
        }
        response = self._request("PUT", f"/contacts/{contact_id}", json=payload)
        if response.status_code not in (200, 204):
            raise RuntimeError(
                f"update_contact_field failed ({response.status_code}): {response.text}"
            )
        return {"success": True, "contact_id": contact_id}

    def update_multiple_fields(
        self, contact_id: str, fields: dict[str, Any]
    ) -> dict[str, Any]:
        payload = {
            "customFields": [
                {"key": self._field_key(k), "field_value": str(v)}
                for k, v in fields.items()
            ]
        }
        response = self._request("PUT", f"/contacts/{contact_id}", json=payload)
        if response.status_code not in (200, 204):
            raise RuntimeError(
                f"update_multiple_fields failed ({response.status_code}): {response.text}"
            )
        return {"success": True, "contact_id": contact_id, "fields_updated": len(fields)}

    def create_opportunity(
        self,
        contact_id: str,
        title: str,
        amount: float,
        pipeline_id: str = "",
        status: str = "open",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "locationId": self.location_id,
            "contactId": contact_id,
            "name": title,
            "monetaryValue": amount,
            "status": status,
        }
        if pipeline_id:
            payload["pipelineId"] = pipeline_id
        response = self._request("POST", "/opportunities/", json=payload)
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"create_opportunity failed ({response.status_code}): {response.text}"
            )
        body = response.json()
        opp = body.get("opportunity", body)
        return {"success": True, "opportunity_id": opp.get("id")}

    def execute_workflow(self, workflow_id: str, contact_id: str) -> dict[str, Any]:
        payload = {"contactId": contact_id}
        response = self._request(
            "POST", f"/workflows/{workflow_id}/trigger", json=payload
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"execute_workflow failed ({response.status_code}): {response.text}"
            )
        return {"success": True}

    def test_connection(self) -> bool:
        try:
            self.get_custom_fields()
            return True
        except Exception as exc:
            logger.error("GHL connection test failed: %s", exc)
            return False
