import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, flt, fmt_money, get_last_day, getdate

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
from erpnext.accounts.doctype.budget.budget import (
	validate_budget_records,)
from erpnext.accounts.utils import get_fiscal_year

def validate_expense_against_budget(args, expense_amount=0):
	args = frappe._dict(args)
	if args.get("company") and not args.fiscal_year:
		args.fiscal_year = get_fiscal_year(args.get("posting_date"), company=args.get("company"))[0]
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

		if (
			args.get(budget_against)
			and args.account
			and frappe.db.get_value("Account", {"name": args.account, "root_type": "Expense"})
		):

			doctype = dimension.get("document_type")

			if frappe.get_cached_value("DocType", doctype, "is_tree"):
				lft, rgt = frappe.db.get_value(doctype, args.get(budget_against), ["lft", "rgt"])
				condition = """and exists(select name from `tab%s`
					where lft<=%s and rgt>=%s and name=b.%s)""" % (
					doctype,
					lft,
					rgt,
					budget_against,
				)  # nosec
				args.is_tree = True
			else:
				condition = "and b.%s=%s" % (budget_against, frappe.db.escape(args.get(budget_against)))
				args.is_tree = False

			args.budget_against_field = budget_against
			args.budget_against_doctype = doctype

			budget_records = frappe.db.sql(
				"""
				select
					b.{budget_against_field} as budget_against, ba.budget_amount, b.monthly_distribution,
					ifnull(b.applicable_on_material_request, 0) as for_material_request,
					ifnull(applicable_on_purchase_order, 0) as for_purchase_order,
					ifnull(applicable_on_booking_actual_expenses,0) as for_actual_expenses,
					b.action_if_annual_budget_exceeded, b.action_if_accumulated_monthly_budget_exceeded,
					b.action_if_annual_budget_exceeded_on_mr, b.action_if_accumulated_monthly_budget_exceeded_on_mr,
					b.action_if_annual_budget_exceeded_on_po, b.action_if_accumulated_monthly_budget_exceeded_on_po
				from
					`tabBudget` b, `tabBudget Account` ba
				where
					b.name=ba.parent and b.fiscal_year <=%s
					and ba.account=%s and b.docstatus=1
					{condition}
			""".format(
					condition=condition, budget_against_field=budget_against
				),
				(args.fiscal_year, args.account),
				as_dict=True,
			)  # nosec

			if budget_records:
				validate_budget_records(args, budget_records, expense_amount)
    
def get_other_condition(args, budget, for_doc):
	condition = "expense_account = '%s'" % (args.expense_account)
	budget_against_field = args.get("budget_against_field")

	if budget_against_field and args.get(budget_against_field):
		condition += " and child.%s = '%s'" % (budget_against_field, args.get(budget_against_field))

	if args.get("fiscal_year"):
		date_field = "schedule_date" if for_doc == "Material Request" else "transaction_date"
		start_date, end_date = frappe.db.get_value(
			"Fiscal Year", args.get("fiscal_year"), ["custom_budget_year_start_date", "custom_budget_year_end_date"]
		)

		condition += """ and parent.%s
			between '%s' and '%s' """ % (
			date_field,
			start_date,
			end_date,
		)

	return condition