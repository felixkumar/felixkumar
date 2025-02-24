# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # def button_validate(self):
    #     res = super(StockPicking, self).button_validate()
    #     if res is True and self.picking_type_code == 'outgoing':
    #         try:
    #             res = self.generate_label_from_shipstation()
    #         except Exception as e:
    #             res = True
    #     return res

    def write(self, values):
        res = super(StockPicking, self).write(values)
        for rec in self:
            if rec and rec.carrier_tracking_ref and rec.sale_id and 'carrier_tracking_ref' not in values.keys():
                rec.sale_id.sudo().write({'carrier_tracking_ref': rec.carrier_tracking_ref})
        return res

    def export_website_delivery_order_using_cron(self):
        wsc_ids = self.env['website.shipstation.configuration'].sudo().search([('is_export', '=', True)])
        for wsc in wsc_ids:
            self.process_website_order_in_shipstation(wsc)
        return True

    def process_website_order_in_shipstation(self, wsc=False):
        if not wsc:
            return False
        _logger.info("Started Exporting Process for WSC {}".format(wsc))
        sale_obj = self.env['sale.order'].sudo()
        sale_ids = sale_obj.search([('website_id', '=', wsc.website_id.id), ('is_exported_to_shipstation', '=', False),
                                    ('state', 'in', ['done', 'sale']),
                                    ('company_id', '=', wsc.website_id.company_id.id)])
        _logger.info("Started Exporting Process for WSC Order Ids{}".format(sale_ids))
        sale_ids.export_website_order_in_shipstation(wsc)
        _logger.info("Done Exporting Process for WSC Order Ids{}".format(sale_ids))
        return True
