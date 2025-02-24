# -*- coding: utf-8 -*-
from odoo import models


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        """
        Use : Inherit create_returns method and mark export_order = False
        for prevent order export validation at time of validate return picking
        """
        res = super(ReturnPicking, self).create_returns()
        picking_id = self.env['stock.picking'].browse(res['res_id'])
        picking_id.write({
            'export_order': False
        })
        return res
