frappe.provide("au_localisation.abn");

frappe.ui.form.on("Customer", {
	async refresh(frm) {
		const enabled = await au_localisation.enabled(frappe.defaults.get_user_default("Company"));
		frm.toggle_display("section_break_abn", enabled);
		frm.fields_dict.tax_id?.$wrapper.find("input").off("blur.au_localisation");
		if (enabled) au_localisation.abn.setup(frm);
	},

	tax_id(frm) {
		// if (!frm.doc.tax_id) {
		// au_localisation.abn.clear_tax_id_fields(frm);
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
