# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

import frappe
# from frappe import _, ValidationError
from frappe.utils import flt
from frappe.model.document import Document

class BudgetElement(Document):
    def on_submit(self):
        add_budget_list(
            self.company,
            self.name,
            self.fiscal_year,
            self.account_no,
            self.budget_amount
        )

@frappe.whitelist()
def add_budget_list(company, budget_element, fiscal_year, account_no, budget_amount):
    entry = {
        "company": company,
        "budget_against": "Budget Element",
        "fiscal_year": fiscal_year,
        "budget_element": budget_element,
        "applicable_on_purchase_order": 1,
        "action_if_annual_budget_exceeded_on_po":"Stop",
        "action_if_accumulated_monthly_budget_exceeded_on_po":"Ignore",
        "applicable_on_booking_actual_expenses": 1,
        "action_if_annual_budget_exceeded": "Stop",
        "action_if_accumulated_monthly_budget_exceeded": "Stop",
        "accounts": [{"account": account_no, "budget_amount": flt(budget_amount)}]
    }

    budget = frappe.new_doc("Budget")
    budget.update(entry)
    budget.insert(ignore_permissions=True, ignore_mandatory=True)
    budget.run_method('submit')
    frappe.db.commit()
