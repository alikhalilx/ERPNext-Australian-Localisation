import json

import frappe
import requests
from frappe import _

from erpnext_australian_localisation.overrides.company import require_enabled


@frappe.whitelist()
def fetch_and_update_abn(tax_id: str, company: str, party_type: str) -> dict:
	require_enabled(company)
	frappe.get_doc("Company", company).check_permission("read")
	if party_type not in ("Supplier", "Customer"):
		frappe.throw(_("Select a Supplier or Customer."))
	frappe.has_permission(party_type, "write", throw=True)
	guid = frappe.db.get_single_value("AU Localisation Settings", "abn_lookup_guid")
	if not guid:
		frappe.throw(_("Configure ABN lookup in AU Localisation Settings first."))
	response = requests.get(
		"https://abr.business.gov.au/json/AbnDetails.aspx",
		params={"abn": tax_id, "guid": guid},
		timeout=20,
	)
	# throws http error when api fails it is an requests library in python
	response.raise_for_status()
	raw = response.text.strip()
	# # JSONP → JSON
	if raw.startswith("callback("):
		raw = raw[len("callback(") : -1]

	data = json.loads(raw)
	message = (data.get("Message") or "").strip()

	if message:
		return {"success": False, "error": message}
	return {
		"success": True,
		"entity_name": data.get("EntityName") or "",
		"business_name": ", ".join(data.get("BusinessName") or [])[:140],
		"abn_status": data.get("AbnStatus") or "",
		"abn_effective_from": data.get("AbnStatusEffectiveFrom") or "",
		"address_postcode": data.get("AddressPostcode") or "",
		"address_state": data.get("AddressState") or "",
	}
