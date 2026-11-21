frappe.ui.form.on("Bank Statement Import", {
	refresh: toggle_import_fields,
	bank_account: toggle_import_fields,
	company: toggle_import_fields,
	bs_download_template(frm) {
		if (!frm.doc.bank_account) {
			frappe.msgprint(__("Please select Bank Account first"));
			return;
		}
		// this is an api method for downloading sample template
		open_url_post(
			"/api/method/erpnext_australian_localisation.overrides.bank_statement_import.download_uploaded_csv_template",
			{
				bank_account: frm.doc.bank_account
			}
		);
	}
});

async function toggle_import_fields(frm) {
	const name = frm.doc.name;
	const bank = frm.doc.bank_account;
	let format;
	if (bank && !frm.is_new() && (await au_localisation.form_enabled(frm))) {
		const { message } = await frappe.db.get_value("Bank Account", bank, [
			"company",
			"bank_statement_format"
		]);
		if (name !== frm.doc.name || bank !== frm.doc.bank_account) return;
		if (message?.company === frm.doc.company) format = message.bank_statement_format;
	}
	frm.toggle_display(["bs_import_file", "bs_download_template"], Boolean(format));
	if (format) {
		frm.set_df_property("bs_import_file", "label", __("Import File ({0})", [format]));
	}
	for (const field of ["google_sheets_url", "import_file", "html_5", "download_template"]) {
		const df = frappe.meta.get_docfield(frm.doctype, field);
		if (df && frm.fields_dict[field])
			frm.set_df_property(field, "hidden", format ? 1 : df.hidden || 0);
	}
}
