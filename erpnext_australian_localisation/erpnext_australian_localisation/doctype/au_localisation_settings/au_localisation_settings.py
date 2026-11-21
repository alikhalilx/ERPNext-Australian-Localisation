# Copyright (c) 2025, frappe.dev@arus.co.in and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AULocalisationSettings(Document):
	def validate(self):
		old = self.get_doc_before_save()
		if [(r.company, r.reporting_period, r.reporting_method) for r in self.bas_reporting_period] != [
			(r.company, r.reporting_period, r.reporting_method)
			for r in (old.bas_reporting_period if old else [])
		]:
			from erpnext_australian_localisation.erpnext_australian_localisation.doctype.au_bas_report.au_bas_report import (
				bas_unavailable,
			)

			bas_unavailable()

	def on_update(self):
		frappe.cache.delete_keys("bootinfo")


@frappe.whitelist()
def is_draft(company):
	bas_report = frappe.get_list("AU BAS Report", filters={"docstatus": 0, "company": company})
	if bas_report:
		return True
	return False


def get_au_email_templates():
	from erpnext_australian_localisation.setup.install_fixtures import get_default_email_templates

	return [record["name"] for record in get_default_email_templates()]


@frappe.whitelist()
def get_disabled_email_templates():
	return frappe.get_all(
		"Email Template",
		filters={"name": ("in", get_au_email_templates()), "enabled": 0},
		pluck="name",
	)


@frappe.whitelist()
def enable_email_templates():
	frappe.get_doc("AU Localisation Settings").check_permission("write")
	enabled = get_disabled_email_templates()
	for template in enabled:
		frappe.db.set_value("Email Template", template, "enabled", 1)

	return enabled
