import frappe


def execute():
	frappe.db.sql(
		"""
			UPDATE `tabAU BAS Report`
			SET
				reporting_method = 'Full reporting method'
		"""
	)
	frappe.db.sql(
		"""
			UPDATE `tabAU BAS Reporting Period`
			SET
				reporting_method = 'Full reporting method'
		"""
	)
