import frappe
from frappe import _

from erpnext_australian_localisation.erpnext_australian_localisation.doctype.payment_batch.payment_batch import (
	_send_remittance_email,
)
from erpnext_australian_localisation.overrides.company import require_enabled


def payment_for_email(docname, party_type):
	doc = frappe.get_doc("Payment Entry", docname)
	doc.check_permission("email")
	require_enabled(doc.company)
	if doc.docstatus != 1 or doc.party_type != party_type:
		frappe.throw(_("Select a submitted payment for the correct party type."))
	return doc


@frappe.whitelist()
def check_party_email(docname: str, party_type: str):
	entry = payment_for_email(docname, party_type)
	email = frappe.db.get_value(
		"Contact",
		{"link_doctype": party_type, "link_name": entry.party, "is_primary_contact": 1},
		"email_id",
	)
	if not email:
		action = _("Remittance Advice") if party_type == "Supplier" else _("Payment Receipt")
		frappe.throw(
			_(
				"Please set a Primary Contact with email address in the {0} master for {1} to send the {2}"
			).format(party_type, entry.party_name, action)
		)
	return True


@frappe.whitelist()
def send_payment_receipt(docname: str):
	doc = payment_for_email(docname, "Customer")

	template = frappe.get_cached_value(
		"AU Localisation Settings", "AU Localisation Settings", "payment_receipt_template"
	)
	if not template:
		frappe.throw(_("Please set a Payment Receipt Template in AU Localisation Settings"))

	email = frappe.db.get_value(
		"Contact",
		{"link_doctype": "Customer", "link_name": doc.party, "is_primary_contact": 1},
		"email_id",
	)

	pe_dict = doc.as_dict()

	template_data = frappe.get_attr("frappe.email.doctype.email_template.email_template.get_email_template")(
		template_name=template,
		doc=frappe.as_json(pe_dict),
	)

	if not template_data:
		frappe.throw(_("Could not render email template"))

	frappe.get_attr("frappe.core.doctype.communication.email.make")(
		doctype="Payment Entry",
		name=docname,
		recipients=email,
		subject=template_data.get("subject"),
		content=template_data.get("message"),
		send_email=1,
		print_format="Payment Receipt",
		print_letterhead=1,
		print_language="en",
		add_css=1,
	)

	return True


@frappe.whitelist()
def send_remittance_email(docname: str):
	payment_for_email(docname, "Supplier")
	template = frappe.get_cached_value(
		"AU Localisation Settings", "AU Localisation Settings", "remittance_advice_template"
	)
	if not template:
		frappe.throw(_("Please set a Remittance Advice Template in AU Localisation Settings"))
	party = frappe.db.get_value(
		"Payment Entry",
		docname,
		"party",
	)

	email = frappe.db.get_value(
		"Contact",
		{"link_doctype": "Supplier", "link_name": party, "is_primary_contact": 1},
		"email_id",
	)

	if email:
		_send_remittance_email(
			payment_entry=docname,
			email=email,
			template=template,
		)
	return True
