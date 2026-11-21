# Copyright (c) 2025, frappe.dev@arus.co.in and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

from erpnext_australian_localisation.erpnext_australian_localisation.doctype.au_bas_report.au_bas_report import (
	bas_unavailable,
)


class AUBASEntry(Document):
	def validate(self):
		bas_unavailable()
