# Copyright (c) 2025, frappe.dev@arus.co.in and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

from erpnext_australian_localisation.overrides.company import require_company_record, require_enabled


class AUSimplerBASReportSetup(Document):
	def validate(self):
		require_enabled(self.company)
		for account in [self.account_1a, self.account_1b, *(row.account for row in self.accounts_g1)]:
			if account:
				require_company_record("Account", account, self.company)
