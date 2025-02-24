# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class SelectPrinter(models.TransientModel):
    _name = "select.printers.wizard"
    _description = "Selection of printers"

    device_ids = fields.Many2many('iot.device', domain=[('type', '=', 'printer')])
    display_device_ids = fields.Many2many('iot.device', relation='display_device_id_select_printer', domain=[('type', '=', 'printer')])

    # TODO: Dead code to remove
    # Since https://github.com/odoo/enterprise/pull/68325 we don't need to select iot anymore
    # For clients that did not upgrade, we keep this method as their old views still call it
    def select_iot(self):
        return {"type": "ir.actions.act_window_close"}
