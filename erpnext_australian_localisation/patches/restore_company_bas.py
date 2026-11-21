from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from erpnext_australian_localisation.overrides.company import initial_company_setup
from erpnext_australian_localisation.setup.create_properties import create_property_setter
from erpnext_australian_localisation.setup.custom_fields import CUSTOM_FIELDS
from erpnext_australian_localisation.setup.property_setters import ABN_PROPERTIES, PROPERTIES


def execute():
	create_custom_fields({"Company": CUSTOM_FIELDS["Company"]}, update=True)
	create_property_setter(PROPERTIES)
	create_property_setter(ABN_PROPERTIES)
	initial_company_setup()
