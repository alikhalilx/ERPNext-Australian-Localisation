frappe.provide("au_localisation.abn");

frappe.ui.form.on("Supplier", {
	async country(frm) {
		if (await au_localisation.enabled(frappe.defaults.get_user_default("Company"))) {
			await frm.set_value("is_allowed_in_pp", frm.doc.country === "Australia" ? 1 : 0);
		}
		return frm.trigger("refresh");
	},
	async refresh(frm) {
		const enabled = await au_localisation.enabled(frappe.defaults.get_user_default("Company"));
		frm.toggle_display("section_break_abn", enabled);
		frm.fields_dict.tax_id?.$wrapper.find("input").off("blur.au_localisation");
		if (enabled) {
			au_localisation.abn.setup(frm);
			set_bank_account_description(frm);
		}
		frm.toggle_display(
			"section_break_au_localisation",
			enabled && frm.doc.country === "Australia"
		);
	},
	async bank_account_no(frm) {
		if (await au_localisation.enabled(frappe.defaults.get_user_default("Company"))) set_bank_account_description(frm);
	},
	tax_id(frm) {
		// if (!frm.doc.tax_id) {
		// 	au_localisation.abn.clear_tax_id_fields(frm);
		// }
		if (frm.doc.is_verify_abn) {
			frm._is_abn_changed = true;
		}
	},

	is_verify_abn(frm) {
		frm._last_abn = null;
		frm._is_abn_changed = false;
		au_localisation.abn.handle_blur(frm);
	},

	async validate(frm) {
		if (
			frm.doc.is_verify_abn &&
			frm._is_abn_changed &&
			(await au_localisation.enabled(frappe.defaults.get_user_default("Company")))
		) {
			frappe.validated = false;
			frm._last_abn = null;
			au_localisation.abn.handle_blur(frm);
		}
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
