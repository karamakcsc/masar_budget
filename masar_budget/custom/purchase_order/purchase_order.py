# import frappe 

# def budget_element_sql(budget_element):
#     return frappe.db.sql("""
#         SELECT name, project, cost_center, account_no 
#         FROM `tabBudget Element` tbe 
#         WHERE name = %s
#     """, (budget_element,), as_dict=True)

# @frappe.whitelist()
# def set_project_value(budget_element):
#     result = budget_element_sql(budget_element)

#     if result:
#         cost_center_py = result[0]['cost_center']
#         project_py = result[0]['project']
#         return {
#             'cost_center_msg': cost_center_py,
#             'project_msg': project_py
#         }
#     else:
#         return {}

# @frappe.whitelist()
# def set_table_value(budget_element):
#     result = budget_element_sql(budget_element)

#     if result:
#         cost_center_py = result[0]['cost_center']
#         project_py = result[0]['project']
#         name_py = result[0]['name']
#         account_no_py = result[0]['account_no']
#         return {
#             'cost_center_msg': cost_center_py,
#             'project_msg': project_py,
#             'name_msg': name_py,
#             'account_no_msg': account_no_py
#         }
#     else:
#         return {}