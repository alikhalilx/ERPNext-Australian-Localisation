frappe.ui.form.on("Payment Entry", {
	company(frm) {
		return frm.trigger("refresh");
	},
	async refresh(frm) {
		const enabled = await au_localisation.form_enabled(frm);
		if (frm._au_print_doc) {
			frm.print_doc = frm._au_print_doc;
			frm.meta.default_print_format = frm._au_previous_print_format;
			delete frm._au_print_doc;
			delete frm._au_previous_print_format;
		}
		if (enabled) {
			frm._au_print_doc = frm.print_doc;
			frm._au_previous_print_format = frm.meta.default_print_format;
			frm.print_doc = () => {
				frm.meta.default_print_format = get_print_format(frm);
				$(".print-preview-sidebar").find('[data-fieldname="print_format"] input').val("");
				frappe.route_options = { frm };
				frappe.set_route("print", frm.doctype, frm.doc.name);
			};
		}
		if (!enabled) return;

		if (frm.doc.docstatus !== 1) return;

		if (frm.doc.party_type === "Customer") {
			frm.add_custom_button(__("Send Payment Receipt"), () => {
				frappe.call({
					method: "erpnext_australian_localisation.overrides.payment_receipt.check_party_email",
					args: { docname: frm.doc.name, party_type: "Customer" },
					callback() {
						frappe.confirm(
							__("Do you want to send the payment receipt email to {0}?", [
								frm.doc.party_name
							]),
							() => {
								frappe.call({
									method: "erpnext_australian_localisation.overrides.payment_receipt.send_payment_receipt",
									args: { docname: frm.doc.name },
									freeze: true,
									freeze_message: __("Sending payment receipt..."),
									callback(r) {
										if (r.message) {
											frappe.show_alert({
												message: __("Payment receipt sent successfully"),
												indicator: "green"
											});
										}
									}
								});
							}
						);
					}
				});
			});
		} else if (frm.doc.party_type === "Supplier") {
			frm.add_custom_button(__("Send Remittance"), () => {
				frappe.call({
					method: "erpnext_australian_localisation.overrides.payment_receipt.check_party_email",
					args: { docname: frm.doc.name, party_type: "Supplier" },
					callback() {
						frappe.confirm(
							__("Do you want to send the remittance advice email to {0}?", [
								frm.doc.party_name
							]),
							() => {
								frappe.call({
									method: "erpnext_australian_localisation.overrides.payment_receipt.send_remittance_email",
									args: { docname: frm.doc.name },
									freeze: true,
									freeze_message: __("Sending remittance advice..."),
									callback(r) {
										if (r.message) {
											frappe.show_alert({
												message: __("Remittance advice sent successfully"),
												indicator: "green"
											});
										}
									}
								});
							}
						);
					}
				});
			});
		}
	}
});

function get_print_format(frm) {
	if (frm.doc.party_type === "Employee") return null;
	if (frm.doc.payment_type === "Pay") return "Remittance Advice";
	if (frm.doc.payment_type === "Receive") return "Payment Receipt";
	return null;
}
