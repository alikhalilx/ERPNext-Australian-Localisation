frappe.ui.form.on("Bank Account", {
	refresh: toggle_bank_fields,
	company: toggle_bank_fields
});

async function toggle_bank_fields(frm) {
	frm.toggle_display("section_break_payment_batch", await au_localisation.form_enabled(frm));
}
