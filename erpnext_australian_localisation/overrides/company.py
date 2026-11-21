import frappe
from frappe import _


def validate(doc, event=None):
	if doc.get("enable_australian_localisation") and doc.country != "Australia":
		frappe.throw(_("Set Country to Australia before enabling Australian localisation."))


def is_enabled(company):
	return bool(
		company
		and frappe.db.exists(
			"Company",
			{
				"name": company,
				"country": "Australia",
				"enable_australian_localisation": 1,
			},
		)
	)


def require_enabled(company):
	if not is_enabled(company):
		frappe.throw(_("Enable Australian localisation for this company first."))


def require_company_record(doctype, name, company):
	if not name or frappe.db.get_value(doctype, name, "company") != company:
		frappe.throw(_("{0} must belong to the selected company.").format(_(doctype)))
