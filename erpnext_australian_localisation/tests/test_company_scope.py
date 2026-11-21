import json

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_australian_localisation.erpnext_australian_localisation.doctype.au_bas_report.au_bas_report import (
	get_gst,
)
from erpnext_australian_localisation.erpnext_australian_localisation.page.payment_proposal.payment_proposal import (
	get_unpaid_entries,
)
from erpnext_australian_localisation.overrides.bank_details_validation import bank_account_validation
from erpnext_australian_localisation.overrides.bank_statement_import import after_save
from erpnext_australian_localisation.overrides.company import is_enabled
from erpnext_australian_localisation.overrides.invoices import on_cancel
from erpnext_australian_localisation.tasks.bas_report import create_scheduled_bas_reports


class TestCompanyScope(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.savepoint("company_scope")
		self.addCleanup(self.rollback_company_setup)

	def rollback_company_setup(self):
		frappe.db.rollback(save_point="company_scope")
		frappe.clear_cache()

	def test_opt_in_and_opt_out(self):
		doc = frappe.get_doc("Company", "_Test AU Company")
		self.assertFalse(is_enabled(doc.name))
		filters = json.dumps(
			{
				"company": doc.name,
				"party_type": "Supplier",
				"created_by": "",
				"from_due_date": "",
				"to_due_date": "",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			get_unpaid_entries(filters)
		for state in (1, 0, 1):
			doc.enable_australian_localisation = state
			doc.save()
			self.assertEqual(is_enabled(doc.name), bool(state))
			bank = frappe._dict(company=doc.name, file_format="ABA", apca_number="invalid")
			if state:
				with self.assertRaises(frappe.ValidationError):
					bank_account_validation(bank, None)
				self.assertEqual(get_unpaid_entries(filters), [])
			else:
				bank_account_validation(bank, None)
			self.assertEqual(frappe.db.count("AU BAS Reporting Period", {"company": doc.name}), 1)
			self.assertEqual(frappe.db.count("AU Simpler BAS Report Setup", {"company": doc.name}), 1)

	def test_saving_company_preserves_reporting_choice(self):
		company = frappe.get_doc("Company", "_Test AU Company")
		company.enable_australian_localisation = 1
		company.save()
		settings = frappe.get_doc("AU Localisation Settings")
		row = next(r for r in settings.bas_reporting_period if r.company == company.name)
		settings.remove(row)
		settings.save()
		company.save()
		self.assertFalse(frappe.db.exists("AU BAS Reporting Period", {"company": company.name}))

	def test_foreign_book(self):
		doc = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": "_Foreign Opt In",
				"abbr": "_FOI",
				"default_currency": "NZD",
				"country": "New Zealand",
				"enable_australian_localisation": 1,
			}
		)
		with self.assertRaisesRegex(frappe.ValidationError, "Set Country to Australia"):
			doc.insert()

	def test_bas_settings_and_scheduling(self):
		company = frappe.get_doc("Company", "_Test AU Company")
		self.assertFalse(frappe.db.exists("AU BAS Reporting Period", {"company": company.name}))
		report = frappe.get_doc(
			{
				"doctype": "AU BAS Report",
				"company": company.name,
				"start_date": "2026-07-01",
				"end_date": "2026-09-30",
			}
		)
		with self.assertRaisesRegex(frappe.ValidationError, "Enable Australian localisation"):
			report.insert()
		company.enable_australian_localisation = 1
		company.save()
		settings = frappe.get_doc("AU Localisation Settings")
		row = next(r for r in settings.bas_reporting_period if r.company == company.name)
		self.assertEqual(row.reporting_period, "Monthly")
		row.reporting_method = "Full reporting method"
		settings.save()
		company.enable_australian_localisation = 0
		company.save()
		create_scheduled_bas_reports()
		self.assertFalse(frappe.db.exists("AU BAS Report", {"company": company.name}))
		company.enable_australian_localisation = 1
		company.save()
		create_scheduled_bas_reports()
		create_scheduled_bas_reports()
		self.assertEqual(frappe.db.count("AU BAS Report", {"company": company.name}), 1)
		self.assertEqual(
			frappe.db.get_value("AU BAS Report", {"company": company.name}, "reporting_method"),
			"Full reporting method",
		)

	def test_cancel_cleans_only_matching_voucher(self):
		company = "_Test AU Company"
		for name, doctype in [("scope-sale", "Sales Invoice"), ("scope-purchase", "Purchase Invoice")]:
			# Two voucher types can use the same document name.
			doc = frappe.new_doc("AU BAS Entry")
			doc.update({"name": name, "company": company, "voucher_type": doctype, "voucher_no": "SCOPE-1"})
			doc.db_insert()
		on_cancel(frappe._dict(doctype="Sales Invoice", name="SCOPE-1", company=company), None)
		self.assertFalse(frappe.db.exists("AU BAS Entry", "scope-sale"))
		self.assertTrue(frappe.db.exists("AU BAS Entry", "scope-purchase"))

	def test_import_requires_an_enabled_book_and_its_bank_account(self):
		company = frappe.get_doc("Company", "_Test AU Company")
		company.enable_australian_localisation = 0
		company.save()
		doc = frappe._dict(
			company=company.name, bank_account="_Unrelated Bank", bs_import_file="synthetic.csv"
		)
		after_save(doc)
		company.enable_australian_localisation = 1
		company.save()
		with self.assertRaisesRegex(frappe.ValidationError, "Bank Account must belong"):
			after_save(doc)
		company.enable_australian_localisation = 0
		company.save()

	def test_post_and_cancel_sales_invoices(self):
		company = frappe.get_doc("Company", "_Test AU Company")
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "_Localisation Customer",
				"customer_group": "Individual",
				"territory": "Australia",
				"customer_type": "Individual",
			}
		).insert()
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "_Localisation Service",
				"item_group": "Services",
				"stock_uom": "Nos",
				"is_stock_item": 0,
			}
		).insert()
		template = frappe.db.get_value(
			"Sales Taxes and Charges Template", {"company": company.name, "title": "AU Sales - GST"}
		)
		self.assertTrue(template)
		for enabled in (0, 1):
			company.enable_australian_localisation = enabled
			company.save()
			invoice = frappe.get_doc(
				{
					"doctype": "Sales Invoice",
					"company": company.name,
					"customer": customer.name,
					"due_date": frappe.utils.today(),
					"taxes_and_charges": template,
					"items": [
						{
							"item_code": item.name,
							"qty": 1,
							"rate": 100,
							"income_account": company.default_income_account,
							"cost_center": company.cost_center,
						}
					],
				}
			)
			invoice.append_taxes_from_master()
			invoice.insert().submit()
			invoice.reload()
			self.assertEqual(invoice.items[0].au_tax_code or "", "AUSGST" if enabled else "")
			self.assertTrue(
				frappe.db.exists("GL Entry", {"company": company.name, "voucher_no": invoice.name})
			)
			bas_filter = {
				"company": company.name,
				"voucher_no": invoice.name,
				"voucher_type": "Sales Invoice",
			}
			self.assertEqual(bool(frappe.db.exists("AU BAS Entry", bas_filter)), bool(enabled))
			if enabled:
				report = frappe.get_doc(
					{
						"doctype": "AU BAS Report",
						"company": company.name,
						"start_date": frappe.utils.today(),
						"end_date": frappe.utils.today(),
						"reporting_method": "Full reporting method",
					}
				).insert()
				for method in ("Full reporting method", "Simpler BAS reporting method"):
					report.reporting_method = method
					report.save()
					get_gst(report.name)
					report.reload()
					self.assertEqual(report.get("1a"), 10, method)
					self.assertEqual(report.g1, 110, method)
			invoice.cancel()
			self.assertFalse(frappe.db.exists("AU BAS Entry", bas_filter))

	def test_purchase_gst_in_both_bas_formats(self):
		company = frappe.get_doc("Company", "_Test AU Company")
		company.enable_australian_localisation = 1
		company.save()
		supplier = frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": "_AU BAS Supplier",
				"supplier_group": "Services",
				"supplier_type": "Company",
			}
		).insert()
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "_AU BAS Purchase",
				"item_group": "Services",
				"stock_uom": "Nos",
				"is_stock_item": 0,
			}
		).insert()
		template = frappe.db.get_value(
			"Purchase Taxes and Charges Template",
			{
				"company": company.name,
				"title": "AU Non Capital Purchase - GST",
			},
		)
		self.assertTrue(template)
		invoice = frappe.get_doc(
			{
				"doctype": "Purchase Invoice",
				"company": company.name,
				"supplier": supplier.name,
				"bill_no": "TEST-AU-001",
				"bill_date": frappe.utils.today(),
				"taxes_and_charges": template,
				"items": [
					{
						"item_code": item.name,
						"qty": 1,
						"rate": 100,
						"expense_account": company.default_expense_account,
						"cost_center": company.cost_center,
					}
				],
			}
		)
		invoice.append_taxes_from_master()
		invoice.insert().submit()
		report = frappe.get_doc(
			{
				"doctype": "AU BAS Report",
				"company": company.name,
				"start_date": frappe.utils.today(),
				"end_date": frappe.utils.today(),
				"reporting_method": "Full reporting method",
			}
		).insert()
		for method in ("Full reporting method", "Simpler BAS reporting method"):
			report.reporting_method = method
			report.save()
			get_gst(report.name)
			report.reload()
			self.assertEqual(report.get("1b"), 10, method)
		invoice.cancel()
		self.assertFalse(
			frappe.db.exists(
				"AU BAS Entry",
				{"company": company.name, "voucher_type": invoice.doctype, "voucher_no": invoice.name},
			)
		)

	def test_shared_party_uses_its_company_context(self):
		from erpnext_australian_localisation.overrides.bank_details_validation import validate_party

		company = frappe.get_doc("Company", "_Test AU Company")
		employee = frappe._dict(doctype="Employee", company=company.name, branch_code="invalid")
		validate_party(employee)
		company.enable_australian_localisation = 1
		company.save()
		with self.assertRaises(frappe.ValidationError):
			validate_party(employee)
