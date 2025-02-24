# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models

class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _get_kitchen_printer(self):
        res = super()._get_kitchen_printer()
        for printer in self.printer_ids:
            if printer.device_identifier:
                res[printer.id]["device_identifier"] = printer.device_identifier
        return res

    def _get_self_ordering_data(self):
        data = super()._get_self_ordering_data()
        data["config"]["iface_print_via_proxy"] = self.iface_print_via_proxy
        data["config"]["iface_printer_id"] = {
            'device_identifier': self.iface_printer_id.identifier,
            'proxy_ip': self.iface_printer_id.iot_ip,
            'printer_type': 'iot'
        }
        return data
