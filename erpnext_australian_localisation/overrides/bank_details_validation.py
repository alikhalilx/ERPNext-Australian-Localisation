import re

import frappe
from frappe import _

from erpnext_australian_localisation.overrides.company import is_enabled


def validate(doc):
	if doc.get("branch_code"):
		pattern = re.compile(r"^\d{6}$")
		branch_code = doc.branch_code.replace("-", "")
		if not pattern.match(branch_code):
			frappe.throw(_("Only 6-digit numbers are allowed in Branch code."))
		else:
			doc.branch_code = branch_code[0:3] + "-" + branch_code[3:]

	if doc.get("bank_account_no"):
		pattern = re.compile(r"^\d{6,10}$")
		if not pattern.match(doc.bank_account_no):
			frappe.throw(_("Only 6 to 10 digit numbers are allowed in Bank Account Number."))


def validate_party(doc, event=None):
	company = doc.company if doc.doctype == "Employee" else frappe.defaults.get_user_default("Company")
	if is_enabled(company):
		validate(doc)


def bank_account_validation(doc, event):
	if is_enabled(doc.company) and doc.file_format != "-None-":
		if doc.apca_number:
			pattern = re.compile(r"^\d{6}$")
			if not pattern.match(doc.apca_number):
				frappe.throw(_("APCA Number must be exactly 6 digits."))

		if doc.fi_abbr:
			pattern = re.compile("^[A-Z]{3}$")
			if not pattern.match(doc.fi_abbr):
				frappe.throw(_("Financial Institution Abbreviation must be three capital letters."))

		validate(doc)
