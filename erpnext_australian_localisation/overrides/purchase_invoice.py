import frappe

from erpnext_australian_localisation.erpnext_australian_localisation.doctype.payment_batch.payment_batch import (
	update_on_payment_entry_updation,
)
from erpnext_australian_localisation.overrides.company import is_enabled


def on_cancel(doc, event):
	batch = frappe.qb.DocType("Payment Batch")
	item = frappe.qb.DocType("Payment Batch Invoice")
	rows = (
		frappe.qb.from_(item)
		.join(batch)
		.on(item.parent == batch.name)
		.select(item.name, item.payment_entry)
		.where(
			(batch.company == doc.company)
			& (batch.docstatus == 0)
			& (item.reference_doctype == doc.doctype)
			& (item.reference_name == doc.name)
		)
	).run(as_dict=True)
	if not rows:
		return
	if is_enabled(doc.company):
		for entry in {row.payment_entry for row in rows if row.payment_entry}:
			update_on_payment_entry_updation(entry)
	else:
		# Retire the cancelled references without starting a new batch workflow.
		frappe.db.delete("Payment Batch Invoice", {"name": ["in", [row.name for row in rows]]})
