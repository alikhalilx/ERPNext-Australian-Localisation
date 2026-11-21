import os
import subprocess

import frappe
from frappe import _
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
from frappe.utils.data import now_datetime


def before_tests():
	if os.environ.get("CI"):
		from erpnext_australian_localisation.tests.check_schema import BASE, ROOT, check

		# Bench can install a shallow checkout in CI.
		if subprocess.run(["git", "cat-file", "-e", BASE], cwd=ROOT, capture_output=True).returncode:
			subprocess.run(
				[
					"git",
					"fetch",
					"--no-tags",
					"--depth=1",
					"https://github.com/Arus-Info/ERPNext-Australian-Localisation.git",
					BASE,
				],
				cwd=ROOT,
				check=True,
			)
		check()
	frappe.clear_cache()
	if not frappe.db.exists("Company", "_Test AU Company"):
		current_year = now_datetime().year
		setup_complete(
			{
				"currency": "AUD",
				"full_name": "_Test User",
				"company_name": "_Test AU Company",
				"timezone": "Australia/Melbourne",
				"company_abbr": "_TAU",
				"industry": "Manufacturing",
				"country": "Australia",
				"fy_start_date": f"{current_year}-01-01",
				"fy_end_date": f"{current_year}-12-31",
				"language": "english",
				"company_tagline": "Testing",
				"email": "test@erpnext.com",
				"password": "test",
				"chart_of_accounts": "Australia - Chart of Accounts with Account Numbers",
			}
		)
		frappe.db.commit()  # nosemgrep
