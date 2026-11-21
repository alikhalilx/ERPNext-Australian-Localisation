frappe.ui.form.on("Payment Entry", {
	async refresh(frm) {
		if (!(await au_localisation.form_enabled(frm))) return;
		if (frm.doc.docstatus !== 1) return;
		const format =
			frm.doc.payment_type === "Receive" ? "Payment Receipt" : "Remittance Advice";
		if (
			["Pay", "Receive"].includes(frm.doc.payment_type) &&
			frm.doc.party_type !== "Employee"
		) {
			frm.add_custom_button(
				__(format),
				() => {
					const query = new URLSearchParams({
						doctype: frm.doctype,
						name: frm.doc.name,
						format
					});
					window.open("/printview?" + query.toString(), "_blank", "noopener");
				},
				__("Print")
			);
		}

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
