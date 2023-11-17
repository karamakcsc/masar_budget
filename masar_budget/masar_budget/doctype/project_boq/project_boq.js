// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

///// filter childtable/////
frappe.ui.form.on('Project BOQ', {
	setup: function (frm) {
		frm.set_query("cost_center", "budget_elements", function (doc, cdt, cdn) {
			var budget_elements = [];

			if (doc.budget_elements && doc.budget_elements.length) {
				budget_elements = doc.budget_elements.map(item => item.cost_center);
			}

			return {
				filters: [
					['Cost Center', 'custom_is_budget', '=', 1],
					['Cost Center', 'name', 'not in', budget_elements],
					['Cost Center', 'is_group', '=', 0]
				]
			};
		});
	},
});


frappe.ui.form.on('Project BOQ', {
	setup: function (frm) {
		frm.set_query("account_no", "budget_elements", function (doc, cdt, cdn) {

			return {
				filters: [
					['Account', 'company', '=', frm.doc.company],
					['Account', 'report_type', '=', 'Profit and Loss'],
					['Account', 'is_group', '=', 0]
				]
			};
		});
	},
});

///// filter childtable siam/////