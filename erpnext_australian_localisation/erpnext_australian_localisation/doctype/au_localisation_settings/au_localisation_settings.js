frappe.ui.form.on("AU Localisation Settings", {
	refresh(frm) {
		frm.toggle_display(["make_tax_category_mandatory", "bas_reporting_period"], false);
		frm.set_intro(__("BAS reporting is unavailable in this release."), "orange");
		set_email_template_notice(frm);
	}
});

async function set_email_template_notice(frm) {
	if (!frappe.boot.versions.crm) {
		return;
	}

	const { message: disabled } = await frappe.call({
		method: "erpnext_australian_localisation.erpnext_australian_localisation.doctype.au_localisation_settings.au_localisation_settings.get_disabled_email_templates"
	});

	if (!disabled?.length) {
		frm.set_df_property("remittance_advice_template", "description", "");
		return;
	}

	frm.set_df_property(
		"remittance_advice_template",
		"description",
		`If  ${frappe.utils.comma_and(disabled)} is not seen in the list of Email Templates,
		<a href="#" class="enable-email-templates">Click Here</a> to see.`
	);

	frm.get_field("remittance_advice_template")
		.$wrapper.off("click", ".enable-email-templates")
		.on("click", ".enable-email-templates", async function (e) {
			e.preventDefault();

			await frappe.call({
				method: "erpnext_australian_localisation.erpnext_australian_localisation.doctype.au_localisation_settings.au_localisation_settings.enable_email_templates",
				freeze: true
			});
			set_email_template_notice(frm);
		});
}
