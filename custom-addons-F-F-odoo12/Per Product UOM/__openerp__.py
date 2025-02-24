# -*- coding: utf-8 -*-
{
    'name': 'Per product UOM',
    'summary': 'Each product can be assigned its own UoM class',
    'category': 'Warehouse',
    'version': '10.1.0',
    'author': 'Nick Ross (CTC corp) - nick (at) theserverexpert (dot) com',
    'website': 'https://github.com/nicknomo/local_addons_odoo',
    'license': 'Other OSI approved licence',
    #'license': 'Creative Commons: Attribution-NonCommercial-ShareAlike 4.0 International',
    # Clarification of NonCommercial: Commercial entities may use this module in Odoo for generating profit,
    # as long as they do not redistribute it.  It cannot be resold, or repackaged in any way.  It cannot be
    # provided as part of a software as a service, nor can it be included in any publicly distributed Odoo builds.
    # If you wish to include this module in an Odoo package, distribution or SaaS deployment, please contact me first.
    # Depending on the usage, I may license it cheaply or for no cost.
    # All entities using their own instance of Odoo, in the course of their business, are free to use this product
    'depends': ['product','sale','stock','purchase'],
    'data': ['views/per_product_uom.xml','views/sales.xml','views/purchase.xml','security/ir.model.access.csv'],
}
