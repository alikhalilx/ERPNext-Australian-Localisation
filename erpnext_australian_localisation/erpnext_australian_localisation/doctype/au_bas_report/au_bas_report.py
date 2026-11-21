import frappe
from frappe import _
from frappe.model.document import Document


def bas_unavailable():
	frappe.throw(_("BAS reporting is unavailable in this release. Cash-basis reporting is deferred."))


class AUBASReport(Document):
	def validate(self):
		bas_unavailable()

	def before_submit(self):
		bas_unavailable()


@frappe.whitelist()
def get_gst(name):
	bas_unavailable()
