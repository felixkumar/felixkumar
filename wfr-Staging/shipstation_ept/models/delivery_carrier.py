import json
import logging
import base64
from urllib.parse import quote
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    """
    inheriting delivery carrier for shipstation implementation.
    """
    _inherit = 'delivery.carrier'
    _description = 'Delivery Carrier'

    shipstation_instance_id = fields.Many2one("shipstation.instance.ept",  ondelete='restrict')
    ept_shipstation_carrier_id = fields.Many2one('shipstation.carrier.ept',
                                             string="Shipstation Carrier")
    shipstation_weight_uom = fields.Selection([('grams', 'Grams'),
                                               ('pounds', 'Pounds'),
                                               ('ounces', 'Ounces')], default='grams',
                                              string="Supported Weight UoM",
                                              help="Supported Weight UoM by ShipStation")
    delivery_type = fields.Selection(selection_add=[("shipstation_ept", "Shipstation")],
                                     ondelete={'shipstation_ept': 'cascade'})
    package_unit_default = fields.Selection([('inches', 'Inches'),
                                             ('centimeters', 'Centimeters')],
                                            string="Package Unit", default='inches')

    shipstation_service_id = fields.Many2one('shipstation.services.ept', string='Shipstation Service',
                                             help="Shipstation service to use for the order from this carrier.")
    confirmation = fields.Selection([('none', 'None'),
                                     ('delivery', 'Delivery'),
                                     ('signature', 'Signature'),
                                     ('adult_signature', 'Adult Signature'),
                                     ('direct_signature', 'Direct Signature')],
                                    default="none", copy=False,
                                    help="Shipstation order confirmation level for order using this carrier.")
    shipstation_package_id = fields.Many2one('stock.package.type',
                                             string='Shipstation Package',
                                             copy=False,
                                             help="Shipstation package to use for this carrier.")
    get_cheapest_rates = fields.Boolean("Cheapest Carrier Selection ?",
                                        help="True: User need to manually get rates and select the service and package "
                                             "in Delivery order when using this carrier.\n "
                                             "False: Service and package will be required and will automatically "
                                             "set in Delivery Order.", default=False)

    shipstation_weight_uom_id = fields.Many2one('uom.uom',
                                                domain=lambda self: [('category_id.id', '=',
                                                                      self.env.ref('uom.product_uom_categ_kgm').id)],
                                                string='Shipstaion UoM',
                                                help="Set equivalent unit of"
                                                     " measurement according to "
                                                     "provider unit of measurement."
                                                     " For Example, if the provider unit of "
                                                     "measurement is KG then you have to select KG "
                                                     "unit of measurement in the Shipstation Unit of"
                                                     " Measurement field.")
    shipstation_carrier_code = fields.Char(string="Shipstation Requested Shipping Service Name")
    ept_shipstation_carrier_ids = fields.Many2many('shipstation.carrier.ept',
                                             string="Shipstation Carriers")
    shipstation_service_ids = fields.Many2many('shipstation.services.ept', string='Shipstation Services',
                                            help="Shipstation service to use for the order from this carrier.")

    def shipstation_ept_send_shipping(self, pickings):
        """
        This method is created to fetch shipstaion labels for the pickings
        if Delivery Order is fulfilled from odoo.
        @param pickings: Contains the value of stock.picking
        """
        result = []
        picking_ids = pickings.filtered(lambda x: not x.export_order)
        for picking in picking_ids:
            if not self._context.get('from_delivery_order', True):
                result = picking.with_context(from_delivery_order=True).get_shipstation_label()
            else:
                result = picking.get_shipstation_label()
        if not result:
            result += [{'exact_price': 0.0, 'tracking_number': ''}]
        return result

    def shipstation_ept_rate_shipment(self, orders):
        """
        This method is to fetch rates from shipstation, when requesting from website or sale order.
        :param orders: record of sale.order
        :return: it will return the price for cheapest carrier service and set
        the service,store and instance in the sale.order
        """
        price = 0.0
        for order in orders:
            if (not self.shipstation_service_id or not self.shipstation_package_id) and self.get_cheapest_rates is False:
                msg = "There are multiple rates available on the Shipstation therefore rate will be available on the Delivery Order."
                return {'success': False, 'price': float(price), 'error_message': msg, 'warning_message': False}
            shipstation_warehouse = self.env['shipstation.warehouse.ept'].search(
                ['|', ('odoo_warehouse_id', '=', order.warehouse_id.id),
                 ('is_default', '=', True),
                 ('shipstation_instance_id', '=', self.shipstation_instance_id.id)], limit=1)
            if shipstation_warehouse:
                shipstation_service_obj = self.env['shipstation.services.ept']
                shipstation_services = self.shipstation_service_id
                shipstation_carriers = shipstation_services.ept_shipstation_carrier_id
                data = {"serviceCode": shipstation_services.service_code,
                        "packageCode": self.shipstation_package_id.shipper_package_code or 'package'}
                instance = self.shipstation_instance_id
                shipping_partner_id = order.partner_shipping_id
                total_weight = sum([(line.product_id.weight * line.product_uom_qty) for line in
                                    order.order_line]) or 0.0
                try:
                    total_weight = self.convert_weight_for_shipstation(
                        order.company_id and order.company_id.get_weight_uom_id(),
                        self.shipstation_weight_uom_id, total_weight)
                except Exception as e:
                    return {'success': False, 'price': float(price),
                            'error_message': "Something went wrong while converting weight",
                            'warning_message': False}
                # check cheapest rate is enabled
                if self.get_cheapest_rates is True:
                    shipstation_carriers = self.ept_shipstation_carrier_ids
                    data = {"packageCode": self.shipstation_package_id.shipper_package_code or 'package'}
                cheapest_carriers = []

                cheapest_carriers_vals = self.get_cheapest_carriers(cheapest_carriers, price, shipstation_carriers, data, shipstation_warehouse, shipping_partner_id, total_weight, instance, order, shipstation_service_obj)

                cheapest_carriers = cheapest_carriers_vals.get('cheapest_carriers')
                code = cheapest_carriers_vals.get('code')
                if cheapest_carriers:
                    finalised_carrier = sorted(cheapest_carriers, key=lambda x: x['price'])
                    price = finalised_carrier[0]['price']
                    service_id = self.env['shipstation.services.ept'].search([
                        ('service_code', '=', finalised_carrier[0]['servicecode']),
                        ('ept_shipstation_carrier_id', '=', finalised_carrier[0]['carrier'].id)])
                    carrier = finalised_carrier[0]['carrier']
                    order.cheapest_service_id = service_id
                    price = self.convert_shipping_rate(price, carrier.carrier_rate_currency_id, order)
                    return {'success': True, 'price': float(price), 'error_message': False, 'warning_message': False}
                else:
                    msg = "115 : Something went wrong while Getting Rates from" \
                          "ShipStation.\n\n %s" % (code.content.decode('utf-8'))
                    _logger.exception(msg)
                    return {
                        'success': False,
                        'price': float(price),
                        'error_message': "No rates available",
                        'warning_message': False
                    }
            else:
                msg = "116 : Warehouse configuration not found while Getting Rates from ShipStation."
                order.unlink_old_message_and_post_new_message(body=msg)
                _logger.exception(msg)
                return {
                    'success': False,
                    'price': float(price),
                    'error_message': "No rates available",
                    'warning_message': False
                }

    def get_data(self, data, carrier, shipstation_warehouse, shipping_partner_id, total_weight):
        data.update({
            "carrierCode": carrier.code,
            "fromPostalCode": shipstation_warehouse.origin_address_id.zip,
            "toState": shipping_partner_id.state_id.code,
            "toCountry": shipping_partner_id.country_id.code,
            "toPostalCode": shipping_partner_id.zip,
            "toCity": shipping_partner_id.city,
            "weight": {
                "value": total_weight,
                "units": self.shipstation_weight_uom
            },
            "confirmation": self.confirmation,
            "residential": False
        })

        if self.shipstation_package_id.packaging_length > 0 and self.shipstation_package_id.width > 0 and self.shipstation_package_id.height > 0:
            data.update({"dimensions": {
                "length": self.shipstation_package_id.packaging_length,
                "width": self.shipstation_package_id.width,
                "height": self.shipstation_package_id.height,
                "units": "inches"
            }})
        return data

    def get_cheapest_carriers(self, cheapest_carriers, price, shipstation_carriers, data, shipstation_warehouse, shipping_partner_id, total_weight, instance, order, shipstation_service_obj):
        for carrier in shipstation_carriers:
            querystring = {'carrierCode': carrier.code}
            data = self.get_data(data, carrier, shipstation_warehouse, shipping_partner_id, total_weight)

            response, code = instance.get_connection(url='/shipments/getrates', data=data, params=querystring,
                                                     method="POST")
            if not response or code.status_code != 200:
                if self.get_cheapest_rates is True:
                    continue
                else:
                    msg = "100 : Something went wrong while Getting Rates from" \
                          "ShipStation.\n\n %s" % (code.content.decode('utf-8'))
                    _logger.exception(msg)
                    return {
                        'success': False,
                        'price': float(price),
                        'error_message': "No rates available",
                        'warning_message': False,
                        'code': code
                    }

            # Filter the cheapest rate based on selected services
            selected_services = self.shipstation_service_ids.filtered(
                lambda x: x.ept_shipstation_carrier_id.id == carrier.id).mapped('service_code')
            for result in response:
                # If response service not exist in selected service then Skip
                if self.get_cheapest_rates and selected_services:
                    if result.get('serviceCode', False) not in selected_services:
                        continue
                # If price not available then Skip
                price = result.get('shipmentCost', False)
                other_cost = result.get('otherCost', False)
                if other_cost:
                    price += other_cost
                service_id = shipstation_service_obj.search(
                    [('service_code', '=', result.get('serviceCode', False)),
                     ('ept_shipstation_carrier_id', '=', carrier.id)])
                # If price not available or service not available then Skip
                if not service_id or not price:
                    continue

                cheapest_carriers.append({
                    'price': price,
                    'servicecode': service_id.service_code,
                    'carrier': carrier
                })
            val = {'cheapest_carriers': cheapest_carriers,
                   'code': code}
            return val

    def shipstation_ept_cancel_shipment(self, picking_ids):
        """This method is used to cancel the picking from the shipstation
        @param picking_ids: This will contains the record of stock.picking
        @return"""
        for picking in picking_ids:
            if picking.ept_shipstation_shipment_id:
                data = {"shipmentId": picking.ept_shipstation_shipment_id}
                instance = picking.shipstation_instance_id
                response, code = instance.get_connection(url='/shipments/voidlabel', data=data, method="POST")
                if code.status_code != 200:
                    try:
                        res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
                    except:
                        res = code.content.decode('utf-8')
                    msg = "101 : Something went wrong while Canceling label on " \
                          "ShipStation.\n\n %s" % res
                    picking.unlink_old_message_and_post_new_message(body=msg)
                    _logger.exception(msg)
                    raise UserError(msg)
                if response.get('approved'):
                    picking.unlink_old_message_and_post_new_message(body="Shipment Cancelled on ShipStation.")
                    picking.write({'canceled_on_shipstation': True})

        return True

    def shipstation_ept_get_tracking_link(self, picking):
        """This method is used to get the tracking link
        @param picking: contains the record of stock.picking
        @return: returns the url link"""
        if self.ept_shipstation_carrier_id.tracking_url:
            if '{TRACKING_NUMBER}' in self.ept_shipstation_carrier_id.tracking_url:
                url = self.ept_shipstation_carrier_id.tracking_url.replace('{TRACKING_NUMBER}',
                                                                       str(picking.carrier_tracking_ref))
            else:
                url = str(self.ept_shipstation_carrier_id.tracking_url) + str(picking.carrier_tracking_ref)
            return url
        elif self.shipstation_instance_id.tracking_link:
            return str(self.shipstation_instance_id.tracking_link) + str(picking.carrier_tracking_ref)
        return False

    def convert_weight_for_shipstation(self, from_uom_unit, to_uom_unit, weight):
        """This will convert the given weight from shipstation
        @param from_uom_unit: value of uom
        @param to_uom_unit: value of uom
        @param weight: Total weight"""
        return from_uom_unit._compute_quantity(weight, to_uom_unit)

    @api.onchange('shipstation_weight_uom')
    def onchange_shipstation_weight_uom(self):
        for rec in self:
            if rec.shipstation_weight_uom:
                mapping_rec = self.env["shipstation.weight.mapping"].search(
                    [('shipstation_weight_uom', '=', rec.shipstation_weight_uom)], limit=1)
            if not mapping_rec:
                raise UserError(
                    "No weight mapping found for {}, Please define first!!!".format(rec.shipstation_weight_uom))
            rec.shipstation_weight_uom_id = mapping_rec.shipstation_weight_uom_id.id

    def convert_shipping_rate(self, amount, from_currency, order):
        """
        Convert shipping rate from carrier currency to order or company currency
        @param amount: Amount to convert
        @param from_currency: Currency id
        @param order: record of sale.order
        @return: will returns the converted amount
        """
        if amount:
            if not from_currency:
                from_currency = order.company_id.currency_id
            rate = self.env['res.currency']._get_conversion_rate(from_currency, order.currency_id,
                                                                 order.company_id, datetime.now())
            return order.currency_id.round(amount * rate)
        return amount
