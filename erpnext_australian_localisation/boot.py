import frappe


def set_bootinfo(bootinfo):
	settings = frappe.get_cached_doc("AU Localisation Settings")
	companies = (
		frappe.get_list(
			"Company",
			filters={"country": "Australia", "enable_australian_localisation": 1},
			pluck="name",
			limit_page_length=0,
		)
		if frappe.has_permission("Company", "read")
		else []
	)
	bootinfo.au_localisation_settings = {
		"enabled_companies": companies,
		"make_tax_category_mandatory": settings.make_tax_category_mandatory,
		"bas_reporting_period": [
			{
				"company": row.company,
				"reporting_period": row.reporting_period,
				"reporting_method": row.reporting_method,
			}
			for row in settings.bas_reporting_period
			if row.company in companies
		],
	}
