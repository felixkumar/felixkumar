# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime



class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = "remaining_days asc, remaining_pdays asc"

    pw_last_sale_id = fields.Many2one('sale.order', string="Last SO", compute="_compute_sale_data")
    pw_last_sale_date = fields.Datetime(string="Last SO Date", related="pw_last_sale_id.date_order")
    pw_last_purchase_id = fields.Many2one('purchase.order', string="Last PO", compute="_compute_purchase_data")
    pw_last_purchase_date = fields.Datetime(string="Last PO Date", related="pw_last_purchase_id.date_order")
    remaining_days = fields.Integer(string='SO Days Since', compute='_compute_remaining_days', store=True)
    remaining_pdays = fields.Integer(string='PO Days Since', compute='_compute_remaining_pdays', store=True)
    pw_purchase_ids = fields.One2many('purchase.order', 'partner_id')
    pw_sale_ids = fields.One2many('sale.order', 'partner_id')

    @api.depends('pw_sale_ids')
    def _compute_sale_data(self):
        for partner in self:
            last_so = self.env['sale.order'].search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ('sale', 'done'))
            ], limit=1, order="id desc")
            partner.pw_last_sale_id = last_so and last_so.id or False

    @api.depends('pw_purchase_ids')
    def _compute_purchase_data(self):
        for partner in self:
            last_po = self.env['purchase.order'].search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ('purchase', 'done'))
            ], limit=1, order="id desc")
            partner.pw_last_purchase_id = last_po and last_po.id or False
            
    @api.depends('pw_last_sale_date')
    def _compute_remaining_days(self):
        for partner in self:
            if partner.pw_last_sale_date:
                delta = datetime.today() - partner.pw_last_sale_date
                partner.remaining_days = delta.days
            else:
                partner.remaining_days = 0
                
    @api.depends('pw_last_purchase_date')
    def _compute_remaining_pdays(self):
        for partner in self:
            if partner.pw_last_purchase_date:
                delta = datetime.today() - partner.pw_last_purchase_date
                partner.remaining_pdays = delta.days
            else:
                partner.remaining_pdays = 0
