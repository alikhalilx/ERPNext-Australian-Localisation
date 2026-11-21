import frappe

from erpnext_australian_localisation.overrides.company import is_enabled


def validate(doc, event):
	if is_enabled(doc.company):
		tax_template = "AU Non Capital Purchase - GST"

		if doc.taxes:
			item_tax_template = ""
		else:
			item_tax_template = "GST Exempt Purchase"

		for field in ["expenses", "taxes"]:
			for i in doc.get(field):
				if i.au_tax_code != "AUSINPTAX":
					tax_code = frappe.db.get_value(
						"AU Tax Determination",
						{
							"bp_tax_template": tax_template,
							"item_tax_template": item_tax_template,
						},
						"tax_code",
					)
					i.au_tax_code = tax_code
