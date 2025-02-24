# -*- coding: utf-8 -*-
# Copyright 2023 IZI PT Solusi Usaha Mudah

from odoo import api, fields, models

class StockWarehouse(models.Model):
    _name = 'stock.warehouse'
    _inherit = 'stock.warehouse'
    
    mp_account_ids = fields.One2many('mp.account', 'warehouse_id')
    
    
# class StockSaleAllocation(models.Model):
#     _name = 'stock.sale.allocation'
#     _description = 'Stock Sale Allocation'
#     
#     product_id = fields.Many2one('product.product')