//// Fetching Leave Type with Filter ///// Start ///Siam

frappe.ui.form.on('Cost Center', {
    setup: function (frm) {
            cur_frm.fields_dict['custom_budget_account'].get_query = function(doc) {
                return {
                    filters: {
                        "report_type": "Profit and Loss",
                        "is_group": 0,
                    }
                };
            };
    }
});

//// Fetching Leave Type with Filter ///// END ///Siam



