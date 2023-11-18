# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _, ValidationError
from frappe.utils import flt
from frappe.model.document import Document

class ProjectBOQ(Document):
    def on_submit(self):
        for budget_element in self.get("budget_elements"):
            add_budget_element(
                self.name,
                self.company,
                budget_element.cost_center,
                self.project,
                self.project_name,
                self.fiscal_year,
                self.posting_date,
                budget_element.account_no,
                budget_element.budget_amount,
            )

@frappe.whitelist()
def add_budget_element(name, company, cost_center, project, project_name, fiscal_year, posting_date, account_no, budget_amount):
    entry = {
        "company": company,
        "cost_center": cost_center,
        "project": project,
        "project_name": project_name,
        "fiscal_year": fiscal_year,
        "posting_date": posting_date,
        "account_no": account_no,
        "budget_amount": flt(budget_amount),
        "project_boq_ref": name
    }

    budget_element = frappe.new_doc("Budget Element")
    budget_element.update(entry)
    budget_element.insert(ignore_permissions=True, ignore_mandatory=True)
    budget_element.run_method('submit')
    frappe.db.commit()