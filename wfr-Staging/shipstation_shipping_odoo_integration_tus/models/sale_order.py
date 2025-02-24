# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta

from odoo import api, fields, models, SUPERUSER_ID

_logger = logging.getLogger("SHIPSTATION INTEGRATION EXT")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    carrier_tracking_ref = fields.Char(string='Tracking Reference', copy=False)
    is_updated_tracking = fields.Boolean("Is Updated Tracking")

    def action_update_tracking_number(self):
        """
        Update Tracking in sale order and in OBL Record from Shipstation

        :return: True If found Tracking number else False
        """
        sale_ids = self.sudo()
        if not sale_ids:
            skipped_days = fields.Datetime.today() - timedelta(days=3)
            sale_ids = self.sudo().search(
                [('shipstation_configuration_id', '!=', False), ('shipstation_order_id', '!=', False),
                 ('state', 'not in', ['draft', 'cancel']), ('is_updated_tracking', '=', False),
                 ('freight_id', '!=', False), ('create_date', '<=', skipped_days),
                 '|', ('freight_id.bol_number', '=', False), ('carrier_tracking_ref', '=', False)], limit=150,
                order='id desc')

        if not sale_ids:
            return False

        configuration = sale_ids[0].shipstation_configuration_id

        _logger.info("*** Start Update Tracking Number ***")

        for count, sale in enumerate(sale_ids):
            # sale.is_updated_tracking = True
            _logger.info("*** Update Tracking Number *** SALE ID {} COUNT {}".format(sale.id, count))
            if sale.carrier_tracking_ref:
                sale.freight_id.bol_number = sale.carrier_tracking_ref
                continue

            url = configuration.making_shipstation_url(
                '/shipments?orderId={0}'.format(sale.shipstation_order_id))
            response_data = sale.shipstation_store_id.shipstation_order_api_calling_function(configuration, url)
            if response_data and response_data.status_code in [200, 204]:
                shipment_data = response_data.json()
                for shipment in shipment_data.get('shipments'):
                    if shipment.get('trackingNumber'):
                        self._cr.execute("""update sale_order set carrier_tracking_ref = '{}' where id={} """.format(
                            shipment.get('trackingNumber'), sale.id))
                        sale.freight_id.bol_number = shipment.get('trackingNumber')

        _logger.info("*** End Update Tracking Number ***")
        if sale_ids:
            sale_ids.write({'is_updated_tracking': True})
            # self._cr.commit()
        return True

    def export_website_order_in_shipstation(self, wsc=False):
        if not wsc:
            return False
        for rec in self:
            _logger.info("Started Process of export Shipstation order {}: ".format(rec))
            out_transfer = rec.picking_ids.filtered(
                lambda p: p.picking_type_code == 'outgoing' and p.company_id.id == rec.company_id.id)
            if out_transfer:
                out_transfer.carrier_id.with_context(
                    shipstation_store=wsc.shipstation_store_id).shipstation_send_shipping(out_transfer)
                template = self.env.ref(
                    'shipstation_shipping_odoo_integration_tus.mail_template_sale_shipstation_in_progress',
                    raise_if_not_found=False)
                if template:
                    template.sudo().send_mail(rec.id, force_send=True)
            _logger.info("Done Process of export Shipstation order {}: ".format(rec))
        return True

    def import_website_exported_delivery_order_using_cron(self):
        sales_order = self.search([('is_exported_to_shipstation', '=', True), ('carrier_tracking_ref', '=', False),
                                   ('shipstation_order_id', '!=', False), ('state', 'in', ['done', 'sale'])])
        shipstation_store_vts_obj = self.env['shipstation.store.vts']
        for sale in sales_order:
            try:
                _logger.info("Sales Order Confirmed  >>>> {0}".format(sale.name))
                shipstation_store_vts_obj.with_company(sale.company_id).update_tracking_carrier(sale,
                                                                                                sale.shipstation_configuration_id,
                                                                                                False)
                _logger.info("Sales Order Tracking Ref Updated  >>>> {0}".format(sale.carrier_tracking_ref))
                # self._cr.commit()
            except Exception as e:
                _logger.warning("Sales Order not Confirmed  >>>> {0} due to >>>> {1}".format(sale.name, e))
                continue

    @api.model_create_multi
    def create(self, vals_list):
        res = super(SaleOrder, self).create(vals_list)
        if res.shipstation_order_id and res.shipstation_store_id:
            store_id = res.edi_store_id.search([('name', '=', res.shipstation_store_id.store_name)], limit=1)
            if not store_id:
                store_id = self.env['edi.customer.store'].create({
                    'name': res.shipstation_store_id.store_name,
                })
            res.edi_store_id = store_id.id
        return res
