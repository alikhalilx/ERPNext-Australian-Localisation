frappe.ui.form.on("AU BAS Report", {
	refresh(frm) {
		frm.disable_save();
		frm.set_intro(
			__("BAS reporting is unavailable in this release. Cash-basis reporting is deferred."),
			"orange"
		);
	}
});
