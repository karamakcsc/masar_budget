from json import loads
from typing import TYPE_CHECKING, List, Optional, Tuple

import frappe
import frappe.defaults
from frappe import _, qb, throw
from frappe.model.meta import get_field_precision
from frappe.query_builder import AliasedQuery, Criterion, Table
from frappe.query_builder.functions import Sum
from frappe.query_builder.utils import DocType
from frappe.utils import (
	cint,
	create_batch,
	cstr,
	flt,
	formatdate,
	get_number_format_info,
	getdate,
	now,
	nowdate,
)
from pypika import Order
from pypika.terms import ExistsCriterion

import erpnext
import masar_budget

# imported to enable erpnext.accounts.utils.get_account_currency
from erpnext.accounts.doctype.account.account import get_account_currency  # noqa
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_dimensions
from erpnext.stock import get_warehouse_account_map
from erpnext.stock.utils import get_stock_value_on

if TYPE_CHECKING:
	from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import RepostItemValuation


class ProjectBOQError(frappe.ValidationError):
	pass

@frappe.whitelist()
def get_budget_year(
	date=None, budget_year=None, label="Date", verbose=1, company=None, as_dict=False, boolean=False
):
	budget_years = get_budget_years(
		date, budget_year, label, verbose, company, as_dict=as_dict, boolean=boolean
	)
	if boolean:
		return budget_years
	else:
		return budget_years[0]


def get_budget_years(
	transaction_date=None,
	fiscal_year=None,
	label="Date",
	verbose=1,
	company=None,
	as_dict=False,
	boolean=False,
):
	budget_years = frappe.cache().hget("budget_years", company) or []

	if not budget_years:
		# if year start date is 2012-04-01, year end date should be 2013-03-31 (hence subdate)
		FY = DocType("Project BOQ")

		query = (
			frappe.qb.from_(FY)
			.select(FY.name, FY.budget_year_start_date, FY.budget_year_end_date)
			.where(FY.disabled == 0)
		)

		if budget_year:
			query = query.where(FY.name == budget_year)

		if company:
			FYC = DocType("Budget Year Company")
			query = query.where(
				ExistsCriterion(frappe.qb.from_(FYC).select(FYC.name).where(FYC.parent == FY.name)).negate()
				| ExistsCriterion(
					frappe.qb.from_(FYC)
					.select(FYC.company)
					.where(FYC.parent == FY.name)
					.where(FYC.company == company)
				)
			)

		query = query.orderby(FY.budget_year_start_date, order=Order.desc)
		budget_years = query.run(as_dict=True)

		frappe.cache().hset("budget_years", company, budget_years)

	if not transaction_date and not budget_year:
		return budget_years

	if transaction_date:
		transaction_date = getdate(transaction_date)

	for fy in budget_years:
		matched = False
		if budget and fy.name == budget_year:
			matched = True

		if (
			transaction_date
			and getdate(fy.budget_year_start_date) <= transaction_date
			and getdate(fy.budget_year_end_date) >= transaction_date
		):
			matched = True

		if matched:
			if as_dict:
				return (fy,)
			else:
				return ((fy.name, fy.budget_year_start_date, fy.budget_year_end_date),)

	error_msg = _("""{0} {1} is not in any active Fiscal Year""").format(
		label, formatdate(transaction_date)
	)
	if company:
		error_msg = _("""{0} for {1}""").format(error_msg, frappe.bold(company))

	if boolean:
		return False

	if verbose == 1:
		frappe.msgprint(error_msg)

	raise ProjectBOQError(error_msg)


@frappe.whitelist()
def get_budget_year_filter_field(company=None):
	field = {"fieldtype": "Select", "options": [], "operator": "Between", "query_value": True}
	budget_years = get_budget_years(company=company)
	for budget_year in budget_years:
		field["options"].append(
			{
				"label": budget_year.name,
				"value": budget_year.name,
				"query_value": [
					budget_year.budget_year_start_date.strftime("%Y-%m-%d"),
					budget_year.budget_year_end_date.strftime("%Y-%m-%d"),
				],
			}
		)
	return field


def validate_budget_year(date, budget_year, company, label="Date", doc=None):
	years = [f[0] for f in get_budget_years(date, label=_(label), company=company)]
	if budget_year not in years:
		if doc:
			doc.budget_year = years[0]
		else:
			throw(_("{0} '{1}' not in Fiscal Year {2}").format(label, formatdate(date), budget_year))