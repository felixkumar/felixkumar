# -*- coding: utf-8 -*-

from odoo import api, models, fields


class ExportFobPrice(models.Model):
    _name = 'export.fob.price'
    _description = "Export FOB Price"

    @api.onchange('fob_amount', 'product_development_id.pro_floor_load_units')
    def _compute_cost(self):
        for rec in self:
            if rec.product_development_id.pro_floor_load_units:
                rec.cost = rec.fob_amount / rec.product_development_id.pro_floor_load_units
            else:
                rec.cost = 0.0

    cost = fields.Float(string="Cost")
    # cost = fields.Float(string="Cost")

    @api.depends('cost', 'product_development_id.export_fob_price')
    def _compute_percentage(self):
        for rec in self:
            if rec.product_development_id.export_fob_price:
                rec.percentage = (rec.cost / rec.product_development_id.export_fob_price) * 100
            else:
                rec.percentage = 0.0

    percentage = fields.Float(string="Percentage (%)", compute='_compute_percentage')
    # percentage = fields.Float(string="Percentage")

    fob_amount = fields.Float(string="Amount")
    commission = fields.Char(string="Cost Name")
    product_development_id = fields.Many2one('product.development', string="Product Development")


class ImportationCost(models.Model):
    _name = 'importation.cost'
    _description = "Importation Cost"

    cost = fields.Float(string="Cost")
    percentage = fields.Float(string="Percentage")
    us_trading = fields.Float(string="Us Trading")
    price_per = fields.Selection([('Per Pallet', 'Per Pallet'),
                                  ('Per Case', 'Per Case'),
                                  ('Per Each', 'Per Each')])
    commission = fields.Char(string="Commission")
    product_development_id = fields.Many2one('product.development', string="Product Development")


class StorageCost(models.Model):
    _name = 'material.cost'
    _description = "Material Cost"

    @api.depends('cost', 'product_development_id.export_fob_price')
    def _compute_percentage(self):
        for rec in self:
            if rec.product_development_id.export_fob_price:
                rec.percentage = (rec.cost / rec.product_development_id.export_fob_price) * 100
            else:
                rec.percentage = 0.0

    cost = fields.Float(string="Cost")
    percentage = fields.Float(string="Percentage", compute='_compute_percentage')
    material_amount = fields.Float(string="Amount")
    price_per = fields.Selection([('Per Pallet', 'Per Pallet'),
                                  ('Per Case', 'Per Case'),
                                  ('Per Each', 'Per Each')])
    commission = fields.Char(string="Commission")
    product_development_id = fields.Many2one('product.development', string="Product Development")


class StorageCost(models.Model):
    _name = 'storage.cost'
    _description = "Storage Cost"

    cost = fields.Float(string="Cost")

    @api.depends('cost', 'product_development_id.export_fob_price')
    def _compute_percentage(self):
        for rec in self:
            if rec.product_development_id.export_fob_price:
                rec.percentage = (rec.cost / rec.product_development_id.export_fob_price) * 100
            else:
                rec.percentage = 0.0

    percentage = fields.Float(string="Percentage", compute='_compute_percentage')
    amount = fields.Float(string="Amount")
    price_per_1 = fields.Selection([('per_pallet', 'Per Pallet'),
                                  ('per_case', 'Per Case'),
                                  ('per_each', 'Per Each')], string='Price Per')
    commission = fields.Char(string="Commission")
    product_development_id = fields.Many2one('product.development', string="Product Development")
