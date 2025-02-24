# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_obl_po_date_range(self):
        freight_ids = self.env['freight.freight'].sudo().search(
            [('account_move_ids', 'in', self.id), ('po_date', '!=', False), ('active', 'in', [False, True])])
        if freight_ids:
            dates = freight_ids.mapped('po_date')
            min_date = min(dates).strftime('%m/%d/%y')
            max_date = max(dates).strftime('%m/%d/%y')
            return "{} to {}".format(min_date, max_date)
        return ""

    def get_obl_ship_date_range(self):
        freight_ids = self.env['freight.freight'].sudo().search(
            [('account_move_ids', 'in', self.id), ('out_date', '!=', False), ('active', 'in', [False, True])])
        if freight_ids:
            dates = freight_ids.mapped('out_date')
            min_date = min(dates).strftime('%m/%d/%y')
            max_date = max(dates).strftime('%m/%d/%y')
            return "{} to {}".format(min_date, max_date)
        return ""
