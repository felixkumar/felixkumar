# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from zeep.helpers import serialize_object

from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.exceptions import UserError
from .fedex_request import FedexRequest, _convert_curr_iso_fdx, _convert_curr_fdx_iso
from .delivery_request_objects import DeliveryCommodity, DeliveryPackage

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def fedex_rate_shipment(self, order):
        if order._name != 'stock.picking':
            return super(DeliveryCarrier, self).fedex_rate_shipment(order)

        is_india = order.partner_id.country_id.code == 'IN' and order.company_id.partner_id.country_id.code == 'IN'

        order_currency = order.company_id.currency_id
        superself = self.sudo()

        # Authentication stuff
        srm = FedexRequest(self.log_xml, request_type="rating", prod_environment=self.prod_environment)
        srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

        # Build basic rating request and set addresses
        srm.transaction_detail(order.name)
        srm.shipment_request(
            self.fedex_droppoff_type,
            self.fedex_service_type,
            self.fedex_default_package_type_id.shipper_package_code,
            self.fedex_weight_unit,
            self.fedex_saturday_delivery,
        )

        srm.set_currency(_convert_curr_iso_fdx(order_currency.name))
        srm.set_shipper(order.company_id.partner_id, order.location_id.warehouse_id.partner_id)
        srm.set_recipient(order.partner_id)

        packages = self._get_packages_from_picking_fedex(order, self.fedex_default_package_type_id)

        for sequence, package in enumerate(packages, 1):
            srm.add_package(
                self,
                package,
                _convert_curr_iso_fdx(package.company_id.currency_id.name),
                sequence_number=sequence,
                mode='rating'
            )

        weight_value = self._fedex_convert_weight(order._get_estimated_weight(), self.fedex_weight_unit)
        srm.set_master_package(weight_value, 1)

        # Commodities for customs declaration (international shipping)
        if 'INTERNATIONAL' in self.fedex_service_type or self.fedex_service_type == 'FEDEX_REGIONAL_ECONOMY' or is_india:
            commodities = self._get_commodities_from_stock_move_lines(order.move_line_ids)
            for commodity in commodities:
                srm.commodities(self, commodity, _convert_curr_iso_fdx(order_currency.name))

            total_commodities_amount = sum(c.monetary_value * c.qty for c in commodities)
            srm.customs_value(_convert_curr_iso_fdx(order_currency.name), total_commodities_amount, "NON_DOCUMENTS")
            srm.duties_payment(order.location_id.warehouse_id.partner_id, superself.fedex_account_number,
                               superself.fedex_duty_payment)

        # Prepare the request
        self._fedex_update_srm(srm, 'rate', picking=order)
        del srm.ClientDetail['Region']
        request = serialize_object(dict(WebAuthenticationDetail=srm.WebAuthenticationDetail,
                                        ClientDetail=srm.ClientDetail,
                                        TransactionDetail=srm.TransactionDetail,
                                        VersionId=srm.VersionId,
                                        RequestedShipment=srm.RequestedShipment))
        self._fedex_add_extra_data_to_request(request, 'rate')
        response = srm.rate(request)

        warnings = response.get('warnings_message')
        if warnings:
            _logger.info(warnings)

        if response.get('errors_message'):
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error:\n%s', response['errors_message']),
                    'warning_message': False}

        price = self._get_picking_request_price(response['price'], order, order_currency)
        return {'success': True,
                'price': price,
                'error_message': False,
                'warning_message': _('Warning:\n%s', warnings) if warnings else False}

    def _get_picking_request_price(self, req_price, picking, order_currency=None):
        """Extract price info in target currency, converting if necessary"""
        if not order_currency:
            order_currency = picking.company_id.currency_id
        company = picking.company_id or self.env.user.company_id
        fdx_currency = _convert_curr_iso_fdx(order_currency.name)
        if fdx_currency in req_price:
            # normally we'll have the order currency on the response, then we can take it as is
            return req_price[fdx_currency]
        _logger.info("Preferred currency has not been found in FedEx response")
        # otherwise, see if we have the company currency, and convert to the order's currency
        fdx_currency = _convert_curr_iso_fdx(company.currency_id.name)
        if fdx_currency in req_price:
            return company.currency_id._convert(
                req_price[fdx_currency], order_currency, company, fields.Date.today())
        # finally, attempt to find active currency in the database
        currency_codes = list(req_price.keys())
        # note, fedex sometimes return the currency as ISO instead of using their own code
        # (eg it can return GBP instead of UKL for a UK address)
        # so we'll do the search for both
        currency_codes += [_convert_curr_fdx_iso(c) for c in currency_codes]
        currency_instances = self.env['res.currency'].search([('name', 'in', currency_codes)])
        currency_by_name = {c.name: c for c in currency_instances}
        for fdx_currency in req_price:
            if fdx_currency in currency_by_name:
                return currency_by_name[fdx_currency]._convert(
                    req_price[fdx_currency], order_currency, company, fields.Date.today())
        _logger.info("No known currency has not been found in FedEx response")
        return 0.0

    def picking_rate_shipment(self, order):
        ''' Compute the price of the order shipment

        :param order: record of sale.order
        :return dict: {'success': boolean,
                       'price': a float,
                       'error_message': a string containing an error message,
                       'warning_message': a string containing a warning message}
                       # TODO maybe the currency code?
        '''
        self.ensure_one()
        if hasattr(self, '%s_rate_shipment' % self.delivery_type):
            res = getattr(self, '%s_rate_shipment' % self.delivery_type)(order)
            # apply fiscal position
            company = self.company_id or order.company_id or self.env.company

            if order._name == 'sale.order':
                fiscal_position_id = order.fiscal_position_id
            else:
                fiscal_position_id = order.sale_id.fiscal_position_id

            res['price'] = self.product_id._get_tax_included_unit_price(
                company,
                company.currency_id,
                fields.Date.today(),
                'sale',
                fiscal_position=fiscal_position_id,
                product_price_unit=res['price'],
                product_currency=company.currency_id
            )
            # apply margin on computed price
            res['price'] = float(res['price']) * (1.0 + (self.margin / 100.0))
            # save the real price in case a free_over rule overide it to 0
            res['carrier_price'] = res['price']
            # free when order is large enough
            return res

    def _get_packages_from_picking_fedex(self, picking, default_package_type):
        packages = []

        if picking.is_return_picking:
            commodities = self._get_commodities_from_stock_move_lines(picking.move_line_ids)
            weight = picking._get_estimated_weight() + default_package_type.base_weight
            packages.append(DeliveryPackage(commodities, weight, default_package_type, currency=picking.company_id.currency_id, picking=picking))
            return packages

        # Create all packages.
        for package in picking.package_ids:
            move_lines = picking.move_line_ids.filtered(lambda ml: ml.result_package_id == package)
            commodities = self._get_commodities_from_stock_move_lines(move_lines)
            package_total_cost = 0.0
            for quant in package.quant_ids:
                package_total_cost += self._product_price_to_company_currency(quant.quantity, quant.product_id, picking.company_id)
            packages.append(DeliveryPackage(commodities, package.shipping_weight or package.weight, package.package_type_id, name=package.name, total_cost=package_total_cost, currency=picking.company_id.currency_id, picking=picking))

        # Create one package: either everything is in pack or nothing is.
        weight_bulk = picking._compute_bulk_weight_fedex()
        if weight_bulk:
            commodities = self._get_commodities_from_stock_move_lines(picking.move_line_ids)
            package_total_cost = 0.0
            for move_line in picking.move_line_ids:
                package_total_cost += self._product_price_to_company_currency(move_line.qty_done, move_line.product_id, picking.company_id)
            packages.append(DeliveryPackage(commodities, weight_bulk, default_package_type, name='Bulk Content', total_cost=package_total_cost, currency=picking.company_id.currency_id, picking=picking))
        elif not packages:
            raise UserError(_("The package cannot be created because the total weight of the products in the picking is 0.0 %s") % (picking.weight_uom_name))

        return packages

    def _get_packages_from_picking(self, picking, default_package_type):
        if self._context.get('params') and self._context.get('params').get('model') == 'freight.freight':
            return self._get_packages_from_picking_fedex(picking=picking, default_package_type=default_package_type)
        packages = super(DeliveryCarrier, self)._get_packages_from_picking(picking=picking,
                                                                           default_package_type=default_package_type)

        return packages
