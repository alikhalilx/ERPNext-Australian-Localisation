# Copyright (c) 2025, frappe.dev@arus.co.in and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AUSimplerBASReportSetup(Document):
	def validate(self):
		from erpnext_australian_localisation.erpnext_australian_localisation.doctype.au_bas_report.au_bas_report import (
			bas_unavailable,
		)

		bas_unavailable()
