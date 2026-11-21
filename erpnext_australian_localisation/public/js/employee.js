frappe.ui.form.on("Employee", {
	async refresh(frm) {
		const enabled = await au_localisation.form_enabled(frm);
		frm.toggle_display("section_break_bank_details", enabled);
		if (enabled) set_bank_account_description(frm);
	},

	company(frm) {
		return frm.trigger("refresh");
	},
	async bank_account_no(frm) {
		if (await au_localisation.form_enabled(frm)) set_bank_account_description(frm);
	}
});

function set_bank_account_description(frm) {
	const account_number = frm.doc.bank_account_no || "";

	if (account_number.length === 10) {
		frm.set_df_property(
			"bank_account_no",
			"description",
			__("10 digit bank account numbers will not be supported for ABA file generation.")
		);
	} else {
		frm.set_df_property("bank_account_no", "description", "");
	}
}
