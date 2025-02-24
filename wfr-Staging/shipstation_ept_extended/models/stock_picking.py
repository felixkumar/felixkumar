import logging
import binascii
import json
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    """
        inheriting stock.picking for implementation of ShipStation ETP.
    """
    _inherit = 'stock.picking'
    _description = 'Stock Picking'

    def button_validate_removed(self, **kwargs):
        """
        REMOVED: As it's not printing anymore another company's record
        """
        self = self.sudo()
        res = False
        for rec in self:
            condition_shipping = False
            if rec.company_id.is_logistics and rec.picking_type_id.code == 'outgoing' and rec.sale_id.company_id.is_oxford:
                try:
                    carrier_id = self.env['delivery.carrier'].search([('is_lowest_cost', '=', True)])
                    rec.carrier_id = carrier_id.id
                    rec.onchange_ept_shipstation_carrier_id()
                    rec.get_rates()
                    delivery_rate_ids = rec.delivery_rate_ids.sorted(key=lambda d: d.total_cost)
                    if delivery_rate_ids:
                        delivery_rate_ids[0].set_service()
                        condition_shipping = True
                except Exception as e:
                    pass

        res = super(StockPicking, self).button_validate()

        for rec in self:
            if condition_shipping:

                product_lines = rec._get_product_lines_from_stock_move_lines(move_lines=rec.move_line_ids)

                move_lines_with_qty_done = rec.move_line_ids.filtered(lambda ml: ml.qty_done > 0)

                product_ids = move_lines_with_qty_done.mapped('product_id')

                if not product_ids:
                    # Print nothing when no move lines where product with quantity_done > 0
                    return res

                # In Odoo 16 there is a wizard to print labels, so we have to use it to avoid overriding
                # a lot of logic related to label format selection / printer selection / etc.
                wizard = rec._init_product_label_layout_wizard(
                    active_model='product.product',
                    picking_quantity='picking',
                    product_ids=product_ids,
                    product_line_ids=product_lines,
                    print_format='dymo',
                )

                res = wizard.process()
        return res

    def write(self, values):
        res = super(StockPicking, self.sudo()).write(values)
        for rec in self.sudo():
            if rec and rec.carrier_tracking_ref and rec.sale_id and 'carrier_tracking_ref' not in values.keys():
                rec.sale_id.sudo().write({'carrier_tracking_ref': rec.carrier_tracking_ref})
        return res

    def get_shipstation_label(self):
        self = self.sudo()
        carrier_id = self.shipstation_service_id.ept_shipstation_carrier_id
        instance = self.shipstation_instance_id
        ship_date = self.date_done.strftime("%Y-%m-%d")
        warehouse = self.picking_type_id.warehouse_id
        self.is_picking_contains_service_and_package()
        ship_from_partner = warehouse.partner_id
        ship_to_partner = self.partner_id
        company_id = self.sale_id.company_id if self.sale_id and (warehouse.company_id != self.sale_id.company_id) else warehouse.company_id
        warehouse_instance_id = self.env['shipstation.warehouse.ept'].search(
            [('shipstation_instance_id', '=', instance.id)], limit=1)

        total_weight = self.get_converted_weight_for_shipstation()

        context = self._context.get('from_delivery_order', True)
        msg = ''
        if not total_weight:
            data_string = "Weight is not set"
            if not context:
                msg += '<br>' + '- ' + data_string
            else:
                raise UserError("{} in Picking : {}".format(data_string, self.name))
        if not carrier_id.code:
            data_string = "Carrier code is not set"
            if not context:
                msg += '<br>' + '- ' + data_string
            else:
                raise UserError("{} in Picking : {}".format(data_string, self.name))
        if not self.shipstation_service_id.service_code:
            data_string = "Service code is not set"
            if not context:
                msg += '<br>' + '- ' + data_string
            else:
                raise UserError("{} in Picking : {}".format(data_string, self.name))
        if not self.shipstation_package_id.shipper_package_code:
            data_string = "Package code is not set"
            if not context:
                msg += '<br>' + '- ' + data_string
            else:
                raise UserError("{} in Picking : {}".format(data_string, self.name))
        if not ship_from_partner.zip:
            data_string = "Postal Code in sender address is not set"
            if not context:
                msg += '<br>' + '- ' + data_string
            else:
                raise UserError("{} in Picking : {}".format(data_string, self.name))
        if ship_from_partner.country_id:
            if not ship_from_partner.country_id.code:
                data_string = "Country code in sender address is not set"
                if not context:
                    msg += '<br>' + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
        else:
            data_string = "Country name in sender address is not set"
            if not context:
                msg += '<br>' + '- ' + data_string
            else:
                raise UserError("{} in Picking : {}".format(data_string, self.name))
        if not ship_to_partner.name:
            data_string = "Delivery partner name is not set"
            if not context:
                msg += '<br>' + '- ' + data_string
            else:
                raise UserError("{} in Picking : {}".format(data_string, self.name))
        if not ship_to_partner.street:
            data_string = "Street in delivery partner address is not set"
            if not context:
                msg += '<br>' + '- ' + data_string
            else:
                raise UserError("{} in Picking : {}".format(data_string, self.name))
        if not ship_to_partner.zip:
            data_string = "Postal code in delivery partner address is not set"
            if not context:
                msg += '<br>' + '- ' + data_string
            else:
                raise UserError("{} in Picking : {}".format(data_string, self.name))
        if ship_to_partner.country_id:
            if not ship_to_partner.country_id.code:
                data_string = "Country code in delivery partner address is not set"
                if not context:
                    msg += '<br>' + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
        else:
            data_string = "Country name in delivery partner address is not set"
            if not context:
                msg += '<br>' + '- ' + data_string
            else:
                raise UserError("{} in Picking : {}".format(data_string, self.name))

        if msg:
            return msg

        length, width, height = self.get_package_dimension()

        data = {
            "carrierCode": carrier_id.code,
            "serviceCode": self.shipstation_service_id.service_code,
            "packageCode": self.shipstation_package_id.shipper_package_code or 'package',
            "confirmation": self.confirmation,
            "shipDate": ship_date,
            "weight": {
                "value": total_weight,
                "units": self.carrier_id.shipstation_weight_uom or self.shipstation_instance_id.shipstation_weight_uom
            },
            "shipFrom": {
                "name": '',  # Warehouse name warehouse_instance_id.name or '',
                "company": company_id.display_name,  # warehouse company name or sale order company name
                "street1": ship_from_partner.street or '',
                "street2": ship_from_partner.street2 or '',
                "city": ship_from_partner.city or '',
                "state": ship_from_partner.state_id.code or '',
                "postalCode": ship_from_partner.zip or '',
                "country": ship_from_partner.country_id.code or '',
                "phone": ship_from_partner.phone or '',
                "residential": ''
            },
            "shipTo": {
                "name": ship_to_partner.name or '',
                "company": ship_to_partner.company_name or (
                        ship_to_partner.parent_id and ship_to_partner.parent_id.name) or '',
                "street1": ship_to_partner.street or '',
                "street2": ship_to_partner.street2 or '',
                "city": ship_to_partner.city or '',
                "state": ship_to_partner.state_id.code or '',
                "postalCode": ship_to_partner.zip or '',
                "country": ship_to_partner.country_id.code or '',
                "phone": ship_to_partner.phone or '',
                "residential": ''
            },
            "testLabel": not self.carrier_id.prod_environment
        }

        if carrier_id and carrier_id.shipping_provider_id:
            data.update({
                "advancedOptions": {
                    "shippingProviderId": self.ept_shipstation_carrier_id.shipping_provider_id
                }
            })

        if length > 0 and width > 0 and height > 0:
            data.update({"dimensions": {
                "length": length,
                "width": width,
                "height": height,
                "units": "inches"
            }})

        response, code = instance.get_connection(url='/shipments/createlabel', data=data, method="POST")
        if code.status_code != 200:
            try:
                res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
            except:
                res = code.content.decode('utf-8')
            msg = "107: Something went wrong while Getting label from " \
                  "ShipStation for Picking : {}.\n\n {}".format(self.name, res)

            _logger.exception(msg)
            if not self._context.get('from_delivery_order', True):
                self.unlink_old_message_and_post_new_message(body=msg)
                return
            else:
                raise UserError(msg)

        binary_data = response.get('labelData', False)
        reference_code = response.get('trackingNumber')
        shipment_id = response.get('shipmentId')
        binary_data = binascii.a2b_base64(str(binary_data))
        message = ("Label created!<br/> <b>Label Tracking Number : </b>%s" % reference_code)
        self.write({'is_get_shipping_label': True,
                    'carrier_tracking_ref': reference_code,
                    'ept_shipstation_shipment_id': shipment_id})
        self.unlink_old_message_and_post_new_message(body=message, attachments=[
            ('Label-%s.%s' % (reference_code, "pdf"), binary_data)])
        shipping_cost = self.convert_company_currency_amount_to_order_currency(response.get('shipmentCost', 0))
        shipping_data = [{
            'exact_price': shipping_cost,
            'tracking_number': reference_code}]
        return shipping_data

    def get_rates(self):
        """
            Calling this method with super user because of accessing multi company record without another company access
        """
        return super(StockPicking, self.sudo()).get_rates()
