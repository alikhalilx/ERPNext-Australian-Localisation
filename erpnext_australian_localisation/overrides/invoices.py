import frappe

from erpnext_australian_localisation.overrides.company import is_enabled


def before_submit(doc, event):
	if not doc.taxes_and_charges or not is_enabled(doc.company):
		return
	sales = doc.doctype == "Sales Invoice"
	template_type = "Sales Taxes and Charges Template" if sales else "Purchase Taxes and Charges Template"
	template = frappe.db.get_value(template_type, doc.taxes_and_charges, "title")
	if sales:
		update_tax_code_for_sales_invoice_item(doc.items, template)
	else:
		update_tax_code_for_purchase_invoice_item(doc.items, template)
	for tax in doc.taxes:
		update_tax_code_for_tax(tax, template)


# update au_tax_code for Sales Invoice Items
def update_tax_code_for_sales_invoice_item(items, tax_template):
	for item in items:
		if item.input_taxed:
			item.au_tax_code = "AUSINPTAX"
		else:
			update_tax_code_for_item(item, tax_template)


# update au_tax_code for Purchase Invoice Items
def update_tax_code_for_purchase_invoice_item(items, tax_template):
	for item in items:
		if item.input_taxed:
			item.au_tax_code = "AUPINPTAX"
		elif item.private_use:
			item.au_tax_code = "AUPPVTUSE"
		else:
			update_tax_code_for_item(item, tax_template)


def update_tax_code_for_item(item, tax_template):
	if item.item_tax_template:
		item_tax_template = frappe.db.get_value("Item Tax Template", item.item_tax_template, "title")
	else:
		item_tax_template = ""

	tax_code = frappe.db.get_value(
		"AU Tax Determination",
		{
			"bp_tax_template": tax_template,
			"item_tax_template": item_tax_template,
		},
		"tax_code",
	)
	item.au_tax_code = tax_code


# update au_tax_code for Taxes and Charges
def update_tax_code_for_tax(tax, tax_template):
	tax_code = frappe.db.get_value(
		"AU Tax Determination",
		{"bp_tax_template": tax_template, "item_tax_template": ""},
		"tax_code",
	)
	tax.au_tax_code = tax_code


def on_cancel(doc, event):
	frappe.db.delete(
		"AU BAS Entry", {"company": doc.company, "voucher_type": doc.doctype, "voucher_no": doc.name}
	)
