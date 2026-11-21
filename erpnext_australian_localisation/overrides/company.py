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


def create_simpler_bas_report_setup(company, chart_of_accounts):
	if not frappe.db.get_value("AU Simpler BAS Report Setup", {"company": company}):
		doc = frappe.new_doc("AU Simpler BAS Report Setup")
		doc.company = company
		if chart_of_accounts == "Australia - Chart of Accounts with Account Numbers":
			accounts = frappe.get_list(
				"Account",
				filters=[
					[
						"account_name",
						"in",
						["Sales Income", "Freight Income", "Other Income", "Service Income"],
					],
					["account_number", "in", ["41010", "41020", "41030", "41040"]],
					["account_type", "=", "Income Account"],
					["company", "=", company],
				],
				pluck="name",
			)
			for account in accounts:
				doc.append("accounts_g1", {"doctype": "Income Account for Simpler BAS", "account": account})

			account_1a = frappe.db.get_value(
				"Account",
				{
					"account_name": "GST Collected (Payable)",
					"account_number": "22010",
					"account_type": "Tax",
					"company": company,
				},
				"name",
			)
			account_1b = frappe.db.get_value(
				"Account",
				{
					"account_name": "GST Paid (Receivable)",
					"account_number": "22020",
					"account_type": "Tax",
					"company": company,
				},
				"name",
			)

			doc.update({"account_1a": account_1a, "account_1b": account_1b})

		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)


def initial_company_setup():
	for company in frappe.get_all(
		"Company",
		filters={"country": "Australia", "enable_australian_localisation": 1},
		fields=["name", "chart_of_accounts"],
	):
		sync_bas_setup(company.name, company.chart_of_accounts)


def on_update(doc, event=None):
	if doc.has_value_changed("enable_australian_localisation"):
		frappe.cache.delete_keys("bootinfo")
		if doc.get("enable_australian_localisation"):
			sync_bas_setup(doc.name, doc.chart_of_accounts)
	elif doc.get("enable_australian_localisation"):
		create_simpler_bas_report_setup(doc.name, doc.chart_of_accounts)


def sync_bas_setup(company, chart_of_accounts):
	settings = frappe.get_doc("AU Localisation Settings", "AU Localisation Settings", for_update=True)
	if not any(row.company == company for row in settings.bas_reporting_period):
		settings.append(
			"bas_reporting_period",
			{
				"company": company,
				"reporting_period": "Monthly",
				"reporting_method": "Simpler BAS reporting method",
			},
		)
		settings.save(ignore_permissions=True)
	create_simpler_bas_report_setup(company, chart_of_accounts)


def on_trash(doc, event):
	if doc.get("enable_australian_localisation"):
		delete_tax_rules(doc.name)
	if frappe.db.exists("AU BAS Reporting Period", {"company": doc.name}):
		remove_bas_reporting_period(doc.name)


def delete_tax_rules(company):
	for tax_rule in frappe.get_all("Tax Rule", filters={"company": company}, pluck="name"):
		frappe.delete_doc("Tax Rule", tax_rule, ignore_permissions=True)


def remove_bas_reporting_period(company):
	au_localisation_settings = frappe.get_doc("AU Localisation Settings")
	rows = [row for row in au_localisation_settings.bas_reporting_period if row.company != company]

	au_localisation_settings.set("bas_reporting_period", rows)
	au_localisation_settings.save(ignore_permissions=True)


def protect_tax_rules(doc, event=None):
	if is_enabled(doc.company) and not any(
		row.doctype_name == "Tax Rule" for row in doc.doctypes_to_be_ignored
	):
		doc.append("doctypes_to_be_ignored", {"doctype_name": "Tax Rule"})
