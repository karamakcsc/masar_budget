
frappe.ui.form.on("Purchase Order", {
    onload: function(frm) {
        var df=frappe.meta.get_docfield("Purchase Order", "cost_center",frm.doc.name);
        df.read_only=1;
        var df=frappe.meta.get_docfield("Purchase Order", "project",frm.doc.name);
        df.read_only=1;
        frm.refresh_fields();
    },
    refresh: function(frm) {
        var df=frappe.meta.get_docfield("Purchase Order", "cost_center",frm.doc.name);
        df.read_only=1;
        var df=frappe.meta.get_docfield("Purchase Order", "project",frm.doc.name);
        df.read_only=1;
        frm.refresh_fields();
    }
    
});
frappe.ui.form.on("Purchase Order Item", {
    item_code: setBudgetDetails,
    validate: setBudgetDetails,
    refresh: setBudgetDetails
});

function setBudgetDetails(frm, cdt, cdn) {
    var d = locals[cdt][cdn];
    if (d.item_code) {
        frappe.call({
            method: "masar_budget.custom.purchase_order.purchase_order.set_table_value",
            args: {
                budget_element: frm.doc.budget_element,
            },
            callback: function (r) {
        
                d.cost_center = r.message.cost_center_msg;
                d.project = r.message.project_msg;
                d.budget_element = r.message.name_msg;
                cur_frm.refresh_field();
            }
        });
    }
}



frappe.ui.form.on('Purchase Order', {
    refresh(frm) {
        if ( !frappe.user.has_role('System Manager') || !frappe.user.has_role('Purchase User') || !frappe.user.has_role('Accounts Manager')) {
            setTimeout(() => {
                frm.remove_custom_button('Update Items');
                frm.remove_custom_button('Purchase Receipt', 'Create');
                frm.remove_custom_button('Subscription', 'Create');
                frm.remove_custom_button('Payment', 'Create');
                frm.remove_custom_button('Purchase Invoice', 'Create');
                frm.remove_custom_button('Payment Request', 'Create');
                frm.remove_custom_button('Hold', 'Status');
                frm.remove_custom_button('Close', 'Status');
                // frm.remove_custom_button('Pick List', 'Create');
                // frm.remove_custom_button('Work Order', 'Create');
                // frm.remove_custom_button('Quotation','Get Items From');
            }, 10);
        }
}
});


//// Fetching Order Type with Filter ///// Start ///Siam

cur_frm.fields_dict['custom_order_type'].get_query = function(doc) {
	return {
		filters: {
			"is_enable": 1
		}
	}
}
//// Fetching Order Type with Filter ///// END ///Siam