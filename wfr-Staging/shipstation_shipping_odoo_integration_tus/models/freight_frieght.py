# -*- coding: utf-8 -*-

import logging
from datetime import date, timedelta, datetime

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class FreightFreight(models.Model):
    _inherit = 'freight.freight'

    def action_update_tracking_number(self):
        """
        Update Tracking in OBL record from Shipstation

        :return: True If found Tracking number else False
        """
        obl_ids = self.sudo()

        configuration = self.env['shipstation.odoo.configuration.vts'].search([], limit=1)
        if not configuration:
            return False

        _logger.info("*** Start Update Tracking Number ***")
        sale_obj = self.env['sale.order'].sudo()

        for count, obl in enumerate(obl_ids):
            # sale.is_updated_tracking = True
            if not obl.shipstation_order_id:
                continue

            _logger.info("*** Update Tracking Number *** OBL ID {} COUNT {}".format(obl.id, count))
            url = configuration.making_shipstation_url('/shipments?orderId={0}'.format(obl.shipstation_order_id))
            sale = obl.sale_id

            if not sale:
                continue
            sale = sale_obj.search([('id', '=', sale)])
            if not sale:
                continue

            response_data = sale.shipstation_store_id.shipstation_order_api_calling_function(configuration, url)
            if response_data and response_data.status_code in [200, 204]:
                shipment_data = response_data.json()
                for shipment in shipment_data.get('shipments'):
                    if shipment.get('trackingNumber'):
                        self._cr.execute("""update sale_order set carrier_tracking_ref = '{}' where id={} """.format(
                            shipment.get('trackingNumber'), sale.id))
                        obl.bol_number = shipment.get('trackingNumber')
                if not shipment_data.get('shipments'):
                    url = configuration.making_shipstation_url(
                        '/fulfillments?orderId={0}'.format(obl.shipstation_order_id))
                    response_data = sale.shipstation_store_id.shipstation_order_api_calling_function(configuration, url)
                    if response_data and response_data.status_code in [200, 204]:
                        shipment_data = response_data.json()
                        for shipment in shipment_data.get('fulfillments'):
                            if shipment.get('trackingNumber'):
                                self._cr.execute(
                                    """update sale_order set carrier_tracking_ref = '{}' where id={} """.format(
                                        shipment.get('trackingNumber'), sale.id))
                                obl.bol_number = shipment.get('trackingNumber')

        _logger.info("*** End Update Tracking Number ***")
        return True
