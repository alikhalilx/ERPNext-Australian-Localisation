frappe.ui.form.on("Item Tax", {
	async item_tax_template(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!row.item_tax_template) return;
		let tax_category = "";
		const { message } = await frappe.db.get_value("Item Tax Template", row.item_tax_template, [
			"title",
			"company"
		]);
		if (!(await au_localisation.enabled(message?.company))) return;
		if (message.title === "GST Exempt Sales") {
			tax_category = "Domestic GST Customer";
		} else if (message.title === "GST Exempt Purchase") {
			tax_category = "Domestic GST Supplier";
		}
		frappe.model.set_value(cdt, cdn, "tax_category", tax_category);
	}
});
