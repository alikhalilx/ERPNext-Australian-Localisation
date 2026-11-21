frappe.ui.form.on("AU Simpler BAS Report Setup", {
	refresh(frm) {
		frm.disable_save();
		frm.set_intro(__("BAS reporting is unavailable in this release."), "orange");
	}
});
