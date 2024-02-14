import frappe
from frappe import _
from erpnext.accounts.doctype.budget.budget import Budget
from frappe.model.document import Document
from frappe.utils import add_months, flt, fmt_money, get_last_day, getdate
from frappe import _, ValidationError
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)

from erpnext.accounts.doctype.budget.budget import (
	validate_budget_records,get_item_details,)
from erpnext.accounts.utils import get_fiscal_year
from masar_budget.utils import get_budget_year

def validate_expense_against_budget(args, expense_amount=0):
    args = frappe._dict(args)
    if args.get("company") and not args.fiscal_year:
        args.fiscal_year = get_fiscal_year(args.get("posting_date"), company=args.get("company"))[0]
        frappe.flags.exception_approver_role = frappe.get_cached_value(
            "Company", args.get("company"), "exception_budget_approver_role"
        )
    args = frappe._dict(args)
    if args.get("company") and not args.fiscal_year:
        args.budget_year = get_budget_year(args.get("posting_date"), company=args.get("company"))[0]
        frappe.flags.exception_approver_role = frappe.get_cached_value(
            "Company", args.get("company"), "exception_budget_approver_role"
        )
    if not args.account:
        args.account = args.get("expense_account")

    if not (args.get("account") and args.get("cost_center")) and args.item_code:
        args.cost_center, args.account = get_item_details(args)

    if not args.account:
        return

    default_dimensions = [
        {
            "fieldname": "project",
            "document_type": "Project",
        },
        {
            "fieldname": "cost_center",
            "document_type": "Cost Center",
        },
    ]

    for dimension in default_dimensions + get_accounting_dimensions(as_list=False):
        budget_against = dimension.get("fieldname")

        # if (
        #     args.get(budget_against)
        #     and args.account
        #     and frappe.db.get_value("Account", {"name": args.account, "root_type": "Expense"})
        # ):

        doctype = dimension.get("document_type")

        if frappe.get_cached_value("DocType", doctype, "is_tree"):
            lft, rgt = frappe.db.get_value(doctype, args.get(budget_against), ["lft", "rgt"])
            condition = """AND EXISTS (SELECT name FROM `tab%s`
                WHERE lft <= %s AND rgt >= %s AND name = b.%s)""" % (
                doctype,
                lft,
                rgt,
                budget_against,
            )
            args.is_tree = True
        else:
            condition = "AND b.%s = %s" % (budget_against, frappe.db.escape(args.get(budget_against)))
            args.is_tree = False

        args.budget_against_field = budget_against
        args.budget_against_doctype = doctype

        budget_records = frappe.db.sql(
            """
            SELECT
                b.{budget_against_field} AS budget_against, ba.budget_amount, b.monthly_distribution,
                IFNULL(b.applicable_on_material_request, 0) AS for_material_request,
                IFNULL(b.applicable_on_purchase_order, 0) AS for_purchase_order,
                IFNULL(b.applicable_on_booking_actual_expenses, 0) AS for_actual_expenses,
                b.action_if_annual_budget_exceeded, b.action_if_accumulated_monthly_budget_exceeded,
                b.action_if_annual_budget_exceeded_on_mr, b.action_if_accumulated_monthly_budget_exceeded_on_mr,
                b.action_if_annual_budget_exceeded_on_po, b.action_if_accumulated_monthly_budget_exceeded_on_po,
                YEAR(tpb.budget_year_end_date) AS budget_years
            FROM
                `tabBudget` b
                INNER JOIN `tabBudget Account` ba ON b.name = ba.parent
                INNER JOIN `tabProject BOQ` tpb ON b.fiscal_year = tpb.fiscal_year
            WHERE
                (b.fiscal_year <= %s and YEAR(tpb.budget_year_end_date) >= %s)
                AND ba.account = %s AND b.docstatus = 1
                {condition}
            """.format(condition=condition, budget_against_field=budget_against),
            (args.fiscal_year, args.fiscal_year, args.account),  # Use args.fiscal_year twice to match the placeholders
            as_dict=True,
        )

        if budget_records:
            validate_budget_records(args, budget_records, expense_amount)


    
def get_other_condition(args, budget, for_doc):
	condition = "expense_account = '%s'" % (args.expense_account)
	budget_against_field = args.get("budget_against_field")

	if budget_against_field and args.get(budget_against_field):
		condition += " and child.%s = '%s'" % (budget_against_field, args.get(budget_against_field))

	if args.get("budget_year"):
		date_field = "schedule_date" if for_doc == "Material Request" else "transaction_date"
		start_date, end_date = frappe.db.get_value(
			"Project BOQ", args.get("budget_year"), ["budget_year_start_date", "budget_year_end_date"]
		)

		condition += """ and parent.%s
			between '%s' and '%s' """ % (
			date_field,
			start_date,
			end_date,
		)

	return condition




class _Budget(Document):
    def validate(self):
        if not self.get(frappe.scrub(self.budget_against)):
            frappe.throw(_("{0} is mandatory").format(self.budget_against))
        self.validate_duplicate()
        # self.validate_accounts()
        self.set_null_value()
        self.validate_applicable_for()

    def validate_accounts(self):
        account_list = []
        for d in self.get("accounts"):
            if d.account:
                account_details = frappe.db.get_value(
                    "Account", d.account, ["is_group", "company", "report_type"], as_dict=1
                )

                # if account_details.is_group:
                #     frappe.throw(_("Budget cannot be assigned against Group Account {0}").format(d.account))
                # elif account_details.company != self.company:
                #     frappe.throw(_("Account {0} does not belongs to company {1}").format(d.account, self.company))
                # elif account_details.report_type != "Profit and Loss":
                #     frappe.throw(
                #         _("Budget cannot be assigned against {0}, as it's not an Income or Expense account").format(
                #             d.account
                #         )
                #     )

                if d.account in account_list:
                    frappe.throw(_("Account {0} has been entered multiple times").format(d.account))
                else:
                    account_list.append(d.account)
