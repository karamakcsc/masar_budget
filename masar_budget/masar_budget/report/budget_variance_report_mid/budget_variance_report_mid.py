# Copyright (c) 2023, KCSC and contributors
# For license information, please see license.txt

import datetime
import frappe
from frappe import _
from frappe.utils import flt, formatdate
from erpnext.controllers.trends import get_period_date_ranges, get_period_month_ranges

def execute(filters=None):
	if not filters:
		filters = {}
	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart_data(filters, columns, data)

	return columns,data , None , chart
def get_data(filters):
    _from, to = filters.get('from_fiscal_year'), filters.get('to_fiscal_year') 
    conditions = ""  
    if filters.get('company'):
        conditions += f"AND tb.company = '{filters.get('company')}' "
    
    if filters.get('budget_against'):
        conditions += f"AND tb.budget_against = '{filters.get('budget_against')}' "
    
    if filters.get("budget_against_filter"):
           conditions += """ AND tb.{budget_against} in (%s)""".format(budget_against=filters.budget_against) % ", ".join(
			["%s"] * len(filters.get("budget_against_filter"))
		)
    data = frappe.db.sql(f"""
        SELECT
            
            tb.budget_element ,
            tba.account,
            tba.budget_amount 
        FROM
            `tabBudget` tb 
            INNER JOIN `tabBudget Account` tba ON tba.parent = tb.name
        WHERE
            tb.docstatus = 1 
            AND tb.fiscal_year BETWEEN {_from} AND {to}
            {conditions}
        ORDER BY tba.budget_amount DESC
    """)

    return data


def get_columns(filters):
	return [
		{
			"label": _(filters.get("budget_against")),
			"fieldtype": "Link",
			"fieldname": "budget_against",
			"options": filters.get("budget_against"),
			"width": 250,
		},
		{
			"label": _("Account"),
			"fieldname": "Account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 500,
		},
        {
			"label": _("Budget"),
			"fieldname": "budget_amount",
			"fieldtype": "data",
			"width": 250,
		},
        
	]


def get_chart_data(filters, columns, data):
    if not data:
        return None
    
    labels = []
    fiscal_year = get_fiscal_years(filters)
    for year in fiscal_year:
        labels.append(year[0])
    
    no_of_columns = len(labels)
    budget_values  ,actual_values= [0] * no_of_columns ,[0] * no_of_columns

    for d in data:
        values = d[2:] 
        index = 0
        for i in range(no_of_columns):
            if index < len(values):
                budget_values[i] += values[index]
            if index + 1 < len(values):
                actual_values[i] += values[index + 1]
            index += 3 
            
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("Budget"), "chartType": "bar", "values": budget_values},
                # {"name": _("Actual Expense"), "chartType": "bar", "values": actual_values},
            ],
        },
        "type": "bar",
    }

def get_fiscal_years(filters):
    fiscal_year = frappe.db.sql(
        """
        select
            name
        from
            `tabFiscal Year`
        where
            name between %(from_fiscal_year)s and %(to_fiscal_year)s
        """,
        {"from_fiscal_year": filters["from_fiscal_year"], "to_fiscal_year": filters["to_fiscal_year"]},
    )
    return fiscal_year
