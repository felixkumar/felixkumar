# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompanyExtend(models.Model):
    _inherit = 'res.company'

    so_double_validation = fields.Selection([
        ('one_step', 'Confirm sale orders in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a sale order')
    ], string="Sale Order Levels of Approvals", default='one_step',
        help="Provide a double validation mechanism for sales")
