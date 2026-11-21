# Copyright (c) 2025, frappe.dev@arus.co.in and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

from erpnext_australian_localisation.overrides.company import require_enabled


class AUBASEntry(Document):
	def validate(self):
		require_enabled(self.company)
