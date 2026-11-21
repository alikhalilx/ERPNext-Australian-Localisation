import json
from types import SimpleNamespace

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_australian_localisation.erpnext_australian_localisation.doctype.au_bas_report.au_bas_report import (
	get_gst,
)
from erpnext_australian_localisation.erpnext_australian_localisation.page.payment_proposal.payment_proposal import (
	get_unpaid_entries,
)
from erpnext_australian_localisation.overrides.bank_details_validation import bank_account_validation
from erpnext_australian_localisation.overrides.company import is_enabled
from erpnext_australian_localisation.overrides.invoices import before_submit, on_cancel
from erpnext_australian_localisation.tasks.bas_report import create_scheduled_bas_reports


class TestCompanyScope(IntegrationTestCase):
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
		invoice = SimpleNamespace(
			doctype="Sales Invoice",
			company=doc.name,
			taxes_and_charges="Domestic",
			items=[frappe._dict(input_taxed=1)],
			taxes=[],
		)
		before_submit(invoice, None)
		self.assertIsNone(invoice.items[0].au_tax_code)
		entries = frappe.db.count("AU BAS Entry", {"company": doc.name})
		for state in (1, 0, 1):
			doc.enable_australian_localisation = state
			doc.save()
			self.assertEqual(is_enabled(doc.name), bool(state))
			bank = frappe._dict(company=doc.name, file_format="ABA", apca_number="invalid")
			if state:
				with self.assertRaises(frappe.ValidationError):
					bank_account_validation(bank, None)
				self.assertEqual(get_unpaid_entries(filters), [])
				before_submit(invoice, None)
				self.assertEqual(invoice.items[0].au_tax_code, "AUSINPTAX")
			else:
				bank_account_validation(bank, None)
			self.assertFalse(frappe.db.exists("AU BAS Reporting Period", {"company": doc.name}))
			self.assertFalse(frappe.db.exists("AU Simpler BAS Report Setup", {"company": doc.name}))
		self.assertEqual(frappe.db.count("AU BAS Entry", {"company": doc.name}), entries)

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

	def test_bas_blocked(self):
		company = "_Test AU Company"
		report = frappe.get_doc(
			{
				"doctype": "AU BAS Report",
				"company": company,
				"start_date": "2026-07-01",
				"end_date": "2026-09-30",
			}
		)
		for action in (
			report.insert,
			report.before_submit,
			lambda: get_gst(report.name),
			frappe.new_doc("AU BAS Entry").validate,
		):
			with self.assertRaisesRegex(frappe.ValidationError, "BAS reporting is unavailable"):
				action()
		create_scheduled_bas_reports()
		self.assertFalse(frappe.db.exists("AU BAS Report", {"company": company}))

	def test_cancel_cleans_only_matching_voucher(self):
		company = "_Test AU Company"
		for name, doctype in [("scope-sale", "Sales Invoice"), ("scope-purchase", "Purchase Invoice")]:
			# Simulate historical entries from a release that supported BAS generation.
			doc = frappe.new_doc("AU BAS Entry")
			doc.update({"name": name, "company": company, "voucher_type": doctype, "voucher_no": "SCOPE-1"})
			doc.db_insert()
		on_cancel(frappe._dict(doctype="Sales Invoice", name="SCOPE-1", company=company), None)
		self.assertFalse(frappe.db.exists("AU BAS Entry", "scope-sale"))
		self.assertTrue(frappe.db.exists("AU BAS Entry", "scope-purchase"))

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
			invoice.set_taxes()
			invoice.insert().submit()
			invoice.reload()
			self.assertEqual(invoice.items[0].au_tax_code or "", "AUSGST" if enabled else "")
			self.assertTrue(
				frappe.db.exists("GL Entry", {"company": company.name, "voucher_no": invoice.name})
			)
			self.assertFalse(
				frappe.db.exists("AU BAS Entry", {"company": company.name, "voucher_no": invoice.name})
			)
			invoice.cancel()

	def test_shared_supplier_is_optional(self):
		meta = frappe.get_meta("Supplier")
		self.assertFalse(meta.get_field("tax_category").mandatory_depends_on)
		self.assertFalse(meta.get_field("branch_code").reqd)
		self.assertNotIn(
			"erpnext_australian_localisation.overrides.bank_details_validation.validate",
			frappe.get_doc_hooks().get("Supplier", {}).get("validate", []),
		)
