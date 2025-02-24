# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Import Users from CSV/Excel file",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Extra Tools",
    "summary": "Import User From CSV Module,  Import  User From Excel App,Import  User from XLS, User From XLSX, User From Excel,User From CSV, User From XLS, User From XLSX Odoo",
    "description": """If you have large records of users in CSV or Excel then using this Odoo app you can import them in Odoo with a single click. This module is useful to import users from CSV/Excel file quickly.
 Import Users From CSV/Excel Odoo
 Import User From CSV Module,  Import User From Excel,Import  User From XLS, Import  User From XLSX Odoo
 Import User From CSV Module,  Import  User From Excel App,Import  User XLS, Import  User From XLSX, User From Excel,  User From CSV,  User From XLS,  User From XLSX Odoo""",
    "version": "14.0.1",
    "depends": [
        "base",
        "sh_message"
    ],
    "application": True,
    "data": [
        "security/import_users_security.xml",
        "security/ir.model.access.csv",
        "wizard/import_user_wizard.xml",
    ],
    "external_dependencies": {
        "python": ["xlrd"],
    },
    "images": ["static/description/background.png", ],
    "live_test_url": "https://youtu.be/ZdByV4mG0Tk",
    "license": "OPL-1",
    "auto_install": False,
    "installable": True,
    "price": 25,
    "currency": "EUR"
}
