# -*- coding: utf-8 -*-
# Copyright (c) 2019 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
import logging
import base64
import json
import requests
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tools.misc import split_every
from datetime import datetime

_logger = logging.getLogger(__name__)


class ShipstationInstanceEpt(models.Model):
    """
    Shipstation Instance Model.
    """
    _name = "shipstation.instance.ept"
    _description = 'Shipstatipn Instance Configuration'

    def _get_company_domain(self):
        """
        Creates domain to only allow to select company from allowed companies in switchboard.
        """
        return [("id", "in", self.env.context.get('allowed_company_ids'))]

    def _compute_delivery_method(self):
        """
        Display Inactive and active delivery method in Shipstation instance.
        @return: Display the active and inactive delivery method.
        """
        delivery_carrier_obj = self.env['delivery.carrier']
        delivery_methods = delivery_carrier_obj.search(
            [('shipstation_instance_id', 'in', self.ids), ('delivery_type', '=', self.provider)])
        self.active_delivery_method = len(delivery_methods)
        inactive_delivery_methods = delivery_carrier_obj.search(
            [('shipstation_instance_id', 'in', self.ids), ('delivery_type', '=', self.provider),
             ('active', '=', False)])
        self.inactive_delivery_method = len(inactive_delivery_methods)

    name = fields.Char(required=True, help="Shipstation instance name.", string="Name")
    provider = fields.Selection([('shipstation_ept', 'Shipstation')], string='Provider', default='shipstation_ept')
    company_id = fields.Many2one('res.company', string="Company", required=True, domain=_get_company_domain)
    service_ids = fields.One2many('shipstation.services.ept', 'shipstation_instance_id', string="Services",
                                  help="services provided By Shipstation instance.")
    active = fields.Boolean('Active', help="If the active field is set to False, then can not access the Instance.",
                            default=True)
    active_delivery_method = fields.Integer(compute='_compute_delivery_method',
                                            help="Hold active delivery count number")
    inactive_delivery_method = fields.Integer(compute='_compute_delivery_method',
                                              help="Hold inactive delivery count number")
    tracking_link = fields.Char(string="Tracking Link",
                                help="Tracking link(URL) useful to track the shipment or package from this URL.",
                                size=256)
    prod_environment = fields.Boolean("Environment",
                                      help="Set to True if your credentials are certified "
                                           "for production.",
                                      default=False)
    shipstation_url = fields.Char(string='ShipStation URL',
                                  default='https://ssapi.shipstation.com',
                                  help="ShipStation Url")
    shipstation_api_key = fields.Char(string='ShipStation API Key',
                                      help="API Key for the ShipStation API access.")
    shipstation_api_secret_key = fields.Char(string='ShipStation Secret Key',
                                             help="API Secret Key for the ShipStation API access.")
    last_import_product = fields.Datetime(string='Last Sync Product')
    shipstation_weight_uom = fields.Selection([('grams', 'Grams'),
                                               ('pounds', 'Pounds'),
                                               ('ounces', 'Ounces')], default='grams',
                                              string="Supported Weight UoM",
                                              help="Supported Weight UoM by ShipStation")
    weight_uom_id = fields.Many2one("uom.uom",
                                    domain=lambda self: [('category_id.id', '=',
                                                          self.env.ref('uom.product_uom_categ_kgm').id)],
                                    help="This UoM will be used while converting the weight in different units of "
                                         "measurement. Set Shipping UoM Same as Supported Weight UoM.")
    shipstation_package_id = fields.Many2one('stock.package.type', string='Shipstation Package')
    shipstation_last_export_order = fields.Datetime(string='Last Export Order')
    active_debug_mode = fields.Boolean(string='Active Debug Mode', copy=False, default=False)

    def action_view_delivery_method(self):
        """
        view of delivery method
        :return: action window for delivery method.
        """
        action = self.env.ref('delivery.action_delivery_carrier_form').read()[0]
        action['domain'] = [('shipstation_instance_id', 'in', self.ids)]
        action['context'] = {'default_shipstation_instance_id': self.ids,
                             'default_delivery_type': self.provider}
        return action

    def unlink(self):
        """
        Delete the Shipstation instance
        @return: Delete the Shipstation Instance.
        """
        delivery_carrier_obj = self.env['delivery.carrier']
        for instance in self:
            delivery_methods = delivery_carrier_obj.search(
                [('shipstation_instance_id', '=', instance.id)])
            inactive_delivery_methods = delivery_carrier_obj.search(
                [('shipstation_instance_id', '=', instance.id), ('active', '=', False)])
            if delivery_methods or inactive_delivery_methods:
                raise UserError(_(
                    "You can not delete %s Shipstation instance because shipstation Methods exist.") % instance.name)
        return super().unlink()

    def toggle_prod_environment(self):
        """
            Toggle status for environment from Instance view.
        """
        self.prod_environment = not self.prod_environment

    def toggle_active(self):
        """
        Active and Inactive the Shipstation instance and All shipstation details.
        """
        res = super().toggle_active()
        for record in self:
            record.is_shipstation_instance_exist()
            crons = self.env['ir.cron'].with_context(active_test=False).search([('name', 'ilike', record.name)])
            if crons:
                crons.write({'active': record.active})

            stores = self.env['shipstation.store.ept'].with_context(active_test=False).search(
                [('shipstation_instance_id', '=', record.id)])
            if stores:
                stores.write({'active': record.active})

            marketplaces = self.env['shipstation.marketplace.ept'].with_context(active_test=False).search(
                [('shipstation_instance_id', '=', record.id)])
            if marketplaces:
                marketplaces.write({'active': record.active})

            carriers = self.env['shipstation.carrier.ept'].with_context(active_test=False).search(
                [('shipstation_instance_id', '=', record.id)])
            if carriers:
                carriers.write({'active': record.active})

            warehouses = self.env['shipstation.warehouse.ept'].with_context(active_test=False).search(
                [('shipstation_instance_id', '=', record.id)])
            if warehouses:
                warehouses.write({'active': record.active})

            services = self.env['shipstation.services.ept'].with_context(active_test=False).search(
                [('shipstation_instance_id', '=', record.id)])
            if services:
                services.write({'active': record.active})

            delivery_methods = self.env['delivery.carrier'].with_context(active_test=False).search(
                [('shipstation_instance_id', '=', record.ids)])
            if delivery_methods:
                delivery_methods.write({'active': record.active})
        return res

    @api.model
    def _get_default_company_id(self):
        return self.env.user.company_id.id

    def create_shipping_product(self):
        product_id = self.env['product.product'].search([('default_code', '=', 'SHIP_SHIPSTATION'),
                                                         ('company_id', '=', self.company_id.id)])
        if not product_id:
            self.env['product.product'].create({'name': 'Shipstation Shipping and Handling',
                                                'type': 'service',
                                                'default_code': 'SHIP_SHIPSTATION',
                                                'list_price': 0.0,
                                                'standard_price': 0.0,
                                                'company_id': self.company_id.id
                                                })

    @api.model
    def create(self, vals):
        self.env['shipstation.weight.mapping'].auto_shipstation_weight_mapping()
        res = super().create(vals)
        res.is_shipstation_instance_exist()
        res.create_shipping_product()
        res.test_shipstation_connection()

        mapping_rec = self.env["shipstation.weight.mapping"].search(
            [('shipstation_weight_uom', '=', res.shipstation_weight_uom)], limit=1)
        if mapping_rec:
            res.weight_uom_id = mapping_rec.shipstation_weight_uom_id.id or False
        return res

    @api.model
    def get_shipstation_api_object(self):
        response, code = self.get_connection(url='/stores/marketplaces', method="GET")
        if code.status_code == 200:
            return code.status_code
        else:
            raise UserError('Given credentials are invalid, please provide valid credentials.')

    def reset_credentials(self):
        return {
                'name': _("Reset Credentials"),
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': self.env.ref('shipstation_ept.shipstation_reset_credentials').id,
                'res_model': 'shipstation.instance.ept',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new',
            }

    def save_credentials(self):
        vals = {}
        vals['shipstation_api_key'] = self.shipstation_api_key
        vals['shipstation_api_secret_key'] = self.shipstation_api_secret_key
        res = super(ShipstationInstanceEpt, self).write(vals)
        return res

    def test_shipstation_connection(self):
        """
        - This method is used to test connection of shipstation instance
        - If authentication provided is correct it will display message of
        'Service working properly'. Else it will raise warning that
        credentials are incorrect.
        """
        response, error = self.make_request_and_get_response_data('/stores/marketplaces', {})
        if error:
            raise UserError('Given credentials are incorrect, please provide correct credentials.')
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': 'ShipStation Connection Successful.',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def view_shipstation_marketplace(self):
        tree_view_id = self.env.ref('shipstation_ept.shipstation_marketplace_tree_view_ept',
                                    False).id
        form_view_id = self.env.ref('shipstation_ept.shipstation_marketplace_form_view_ept',
                                    False).id
        return {
            'name': 'ShipStation Marketplaces',
            'view_mode': 'tree',
            'domain': [('shipstation_instance_id', '=', self.id)],
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'res_model': 'shipstation.marketplace.ept',
            'type': 'ir.actions.act_window',

        }

    def view_shipstation_stores(self):
        tree_view_id = self.env.ref('shipstation_ept.shipstation_store_tree_view_ept', False).id
        form_view_id = self.env.ref('shipstation_ept.shipstation_store_form_view_ept', False).id
        return {
            'name': 'ShipStation Stores',
            'view_mode': 'tree',
            'domain': [('shipstation_instance_id', '=', self.id)],
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'res_model': 'shipstation.store.ept',
            'type': 'ir.actions.act_window',

        }

    def view_shipstation_carrier(self):
        tree_view_id = self.env.ref('shipstation_ept.shipstation_carrier_tree_view_ept', False).id
        form_view_id = self.env.ref('shipstation_ept.shipstation_carrier_form_view_ept', False).id
        return {
            'name': 'ShipStation Carriers',
            'view_mode': 'tree',
            'domain': [('shipstation_instance_id', '=', self.id)],
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'res_model': 'shipstation.carrier.ept',
            'type': 'ir.actions.act_window',

        }

    def view_shipstation_packages(self):
        """
        change form_view_id = self.env.ref('shipstation_ept.form_view_product_packaging', False).id
        instead of self.env.ref('product.product_packaging_form_view', False).id
        New form view created for product_packaging model
        """
        tree_view_id = self.env.ref('stock.stock_package_type_tree', False).id
        form_view_id = self.env.ref('shipstation_ept.form_view_stock_package_type', False).id
        return {
            'name': 'ShipStation Packages',
            'view_mode': 'tree',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'domain': [('shipstation_instance_id', '=', self.id)],
            'res_model': 'stock.package.type',
            'type': 'ir.actions.act_window',
        }

    def view_shipstation_warehouses(self):
        tree_view_id = self.env.ref('shipstation_ept.shipstation_warehouse_tree_view_ept', False).id
        form_view_id = self.env.ref('shipstation_ept.shipstation_warehouse_form_view_ept', False).id
        return {
            'name': 'ShipStation Warehouses',
            'view_mode': 'tree',
            'domain': [('shipstation_instance_id', '=', self.id)],
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'res_model': 'shipstation.warehouse.ept',
            'type': 'ir.actions.act_window',
        }

    def shipstation_sync(self):
        """
            Master sync operations for ShipStation.
        """
        methods = ['stores', 'carriers', 'packages', 'services', 'warehouses']
        for method in methods:
            try:
                getattr(self, "get_shipstation_{}".format(method))()
            except Exception as e:
                # Error code 102
                _logger.exception(
                    "102 Error while syncing {} from ShipStation \n with error {} ".format(method.capitalize(), e))
                raise UserError("102 Error while syncing {} from ShipStation. \n {}".format(method.capitalize(), e))
            self._cr.commit()
            _logger.info("{} Sync Done... Committing to database".format(method.capitalize()))

        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': 'ShipStation Sync is completed',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def get_shipstation_stores(self):
        """
        - This method is used to get and create store of particular instance and
        of particular marketplace.
        - If store of particular marketplace and instance already exists then it will be
        skipped else new record will be created for that particular instance and marketplace.
        """
        shipstation_store_obj = self.env['shipstation.store.ept']
        querystring = {'showInactive': 'false'}
        response, error = self.make_request_and_get_response_data('/stores', querystring)
        if error:
            raise UserError(error)
        for res in response:
            store_id = shipstation_store_obj.search([('shipstation_instance_id', '=', self.id),
                                                     ('shipstation_identification', '=', res.get('storeId', False))],
                                                    limit=1)
            if not store_id:
                vals = self.prepare_vals_for_store(res)
                store_id = shipstation_store_obj.create(vals)
            _logger.info(
                "Instance:{}, Store:{}, Store ID:{} created successfully".format(self.id, store_id.name,
                                                                                 res.get('storeId')))
        return True

    def prepare_vals_for_store(self, res):
        marketplace_id = self.find_or_create_market_place(res)
        return {'name': res.get('storeName', False),
                'shipstation_identification': res.get('storeId', False),
                'marketplace_id': marketplace_id.id,
                'integration_url': res.get('integrationUrl', False),
                'company_name': res.get('companyName', False),
                'active': res.get('active', False),
                'phone': res.get('phone', False),
                'public_email': res.get('publicEmail', False),
                'website': res.get('website', False),
                'shipstation_instance_id': self.id,
                'company_id': self.company_id.id
                }

    def find_or_create_market_place(self, res):
        shipstation_marketplace_obj = self.env['shipstation.marketplace.ept']
        marketplace_id = shipstation_marketplace_obj.search(
            [('shipstation_identification', '=', res.get('marketplaceId')),
             ('shipstation_instance_id', '=', self.id)], limit=1)
        if not marketplace_id:
            marketplace_id = shipstation_marketplace_obj.create({
                'shipstation_identification': res.get('marketplaceId'),
                'name': res.get('marketplaceName'),
                'shipstation_instance_id': self.id,
                'company_id': self.company_id.id
            })
        return marketplace_id

    def get_shipstation_carriers(self):
        """
        - This method is used to get and create carrier of particular instance.
        - If carrier of particular instance already exists then it will be skipped
        else new record will be created for that particular instance.
        """
        company_id = self.company_id.id
        shipstation_carrier_obj = self.env['shipstation.carrier.ept']
        response, error = self.make_request_and_get_response_data('/carriers', {})
        if error:
            raise UserError(error)
        for res in response:
            carrier = shipstation_carrier_obj.search(
                [('shipstation_instance_id', '=', self.id), ('code', '=', res.get('code'))], limit=1)
            if not carrier:
                carrier = shipstation_carrier_obj.create({'name': res.get('name', False),
                                                          'code': res.get('code', False),
                                                          'shipstation_instance_id': self.id,
                                                          'company_id': company_id,
                                                          'shipping_provider_id': res.get('shippingProviderId', '')
                                                          })
            _logger.info(
                "Instance:{}, Shipstation Carrier:{}, Code:{}".format(self.id, carrier.name, carrier.code))
        return True

    def get_shipstation_packages(self):
        """
        - This method is used to get and create package of particular instance and
        of particular carrier.
        - If store of particular carrier and instance already exists then it will be
        skipped else new record will be created for that particular instance and carrier.
        """
        product_package_obj = self.env['stock.package.type']
        ept_shipstation_carrier_ids = self.get_ept_shipstation_carrier_ids()
        for carrier in ept_shipstation_carrier_ids:
            querystring = {'carrierCode': carrier.code}
            response, error = self.make_request_and_get_response_data('/carriers/listpackages', querystring)
            if error:
                _logger.info("Error while sync package for Carrier : {}, Error : {}".format(carrier.name, error))
            else:
                for res in response:
                    package_id = product_package_obj.search(
                        [('package_carrier_type', '=', self.provider),
                         ('ept_shipstation_carrier_id', '=', carrier.id),
                         ('shipper_package_code', '=', res.get('code'))], limit=1)
                    if not package_id:
                        package_id = product_package_obj.create({
                            'name': res.get('name', False),
                            'shipper_package_code': res.get('code', False),
                            'ept_shipstation_carrier_id': carrier.id,
                            'shipstation_instance_id': self.id,
                            'package_carrier_type': self.provider,
                            'company_id': self.company_id.id
                        })
                    _logger.info(
                        "Instance:{}, Shipstation Package:{}, Code:{}".format(self.id, package_id.name,
                                                                              package_id.shipper_package_code))
        return True

    def get_shipstation_services(self):
        """
        - This method is used to get and create service of particular instance and
        of particular carrier.
        - If store of particular carrier and instance already exists then it will
        be skipped else new record will be created for that particular instance and carrier.
        """
        shipstation_service_obj = self.env['shipstation.services.ept']
        ept_shipstation_carrier_ids = self.get_ept_shipstation_carrier_ids()
        for carrier in ept_shipstation_carrier_ids:
            querystring = {'carrierCode': carrier.code}
            response, error = self.make_request_and_get_response_data('/carriers/listservices', querystring)
            if error:
                _logger.info("Error while sync services for Carrier : {}, Error : {}".format(carrier.name, error))
            else:
                for res in response:
                    service_id = shipstation_service_obj.search(
                        [('shipstation_instance_id', '=', self.id),
                         ('ept_shipstation_carrier_id', '=', carrier.id),
                         ('service_code', '=', res.get('code'))], limit=1)
                    if not service_id:
                        if res.get('domestic', False) and res.get('international', False):
                            type = "both"
                        elif res.get('domestic', False):
                            type = "domestic"
                        elif res.get('international', False):
                            type = "international"
                        service_id = shipstation_service_obj.create({
                            'service_name': res.get('name', False),
                            'service_code': res.get('code', False),
                            'service_type': type,
                            'ept_shipstation_carrier_id': carrier.id,
                            'shipstation_instance_id': self.id,
                            'company_id': self.company_id.id,
                        })
                    _logger.info(
                        "Instance:{}, Shipstation Service:{}, Code:{}".format(self.id, service_id.service_name,
                                                                              service_id.service_code))
        return True

    def get_shipstation_warehouses(self):
        """
        - This method is used to get and create warehouse of particular instance.
        - If warehouse of particular instance already exists then it will be skipped
        else new record will be created for that particular instance.
        """
        response, error = self.make_request_and_get_response_data('/warehouses', {})
        if error:
            raise UserError(error)
        shipstation_warehouse_obj = self.env['shipstation.warehouse.ept']
        for res in response:
            warehouse_id = shipstation_warehouse_obj.search(
                [('shipstation_instance_id', '=', self.id),
                 ('shipstation_identification', '=', res.get('warehouseId', False))], limit=1)
            if not warehouse_id:
                origin_partner = self.compute_partner_address(res.get('originAddress'))
                return_partner = self.compute_partner_address(res.get('returnAddress'))
                warehouse_id = shipstation_warehouse_obj.create({
                    'name': res.get('warehouseName', False),
                    'is_default': res.get('isDefault', False),
                    'shipstation_identification': res.get('warehouseId', False),
                    'shipstation_instance_id': self.id,
                    'origin_address_id': origin_partner.id,
                    'return_address_id': return_partner.id,
                    'company_id': self.company_id.id
                })
            _logger.info(
                "Instance:{}, Shipstation Warehouse:{}, Identification:{}".format(
                    self.id, warehouse_id.name, warehouse_id.shipstation_identification))
        return True

    def compute_partner_address(self, vals):
        res_partner_obj = self.env['res.partner']

        state_id = self.env['res.country.state'].search(
            [('code', '=', vals.get('state', False))],
            limit=1)
        country_id = self.env['res.country'].search(
            [('code', '=', vals.get('country', False))],
            limit=1)
        address_vals = {
            'name': vals.get('name', False),
            'street': vals.get('street1', False),
            'street2': vals.get('street2', False),
            'city': vals.get('city', False),
            'state_id': state_id.id,
            'zip': vals.get('postalCode', False),
            'country_id': country_id.id,
            'phone': vals.get('phone', False)
        }
        partner = res_partner_obj._find_partner_ept(address_vals,
                                                    list(address_vals.keys()))
        if not partner:
            partner = res_partner_obj.create(address_vals)
        return partner

    def export_to_shipstation_cron(self, ctx={}, store_ids=False, start_date=False, end_date=False):
        instance_id = ctx.get('shipstation_instance_id')
        instance = self.env['shipstation.instance.ept'].browse(instance_id)
        if not instance:
            return True
        domain = [('shipstation_instance_id', '=', instance.id),
                  ('export_order', '=', True),
                  ('is_exported_to_shipstation', '=', False),
                  ('state', '=', 'assigned'), ('exception_counter', '<=', 3)]
        if store_ids:
            domain.append(('ept_shipstation_store_id', 'in', store_ids.ids))
        if instance.shipstation_last_export_order and not start_date and end_date:
            domain.append(
                ('create_date', '>', instance.shipstation_last_export_order.strftime("%Y-%m-%d %H:%M:%S")))
        elif start_date and end_date:
            domain += ([('create_date', '>', start_date.strftime("%Y-%m-%d %H:%M:%S")),
                        ('create_date', '<', end_date.strftime("%Y-%m-%d %H:%M:%S"))])
        model_id = self.env['ir.model'].search([('model', '=', self._name)]).id
        log_line = self.env['common.log.lines.ept']
        pickings = self.env['stock.picking'].search(domain, order='id desc')
        for picking in pickings:
            # if order is to fulfilled from shipstation and it is not exported
            try:
                _logger.info("Exporting picking %s to shipstation", picking.name)
                picking.with_context(from_delivery_order=False).export_order_to_shipstation(log_line)
            except Exception as exception:
                picking.unlink_old_message_and_post_new_message(body=exception)
                msg = "Error : {} comes at the time of exporting order to Shipstation".format(exception)
                log_line.create_common_log_line_ept(message=msg, model_id=model_id,
                                                    res_id=picking.id, operation_type='export',
                                                    module='shipstation_ept',
                                                    log_line_type='fail')
                _logger.exception("103: CRON ERROR while Exporting order %s to shipstation, \
                                ERROR: %s", picking.name, exception)
                continue
        if not start_date:
            instance.write({'shipstation_last_export_order': datetime.now()})

    def make_request_and_get_response_data(self, url, querystring):
        error = ''
        response, code = self.get_connection(url=url, params=querystring, method="GET")
        if code.status_code != 200:
            error = code.content.decode('utf-8')
        return response, error

    def get_ept_shipstation_carrier_ids(self):
        shipstation_carrier_obj = self.env['shipstation.carrier.ept']
        carrier_id = self._context.get('carrier_id')
        domain = [('id', '=', carrier_id)] if carrier_id else [('shipstation_instance_id', '=', self.id)]
        ept_shipstation_carrier_ids = shipstation_carrier_obj.search(domain)
        if not ept_shipstation_carrier_ids and not carrier_id:
            self.get_shipstation_carriers()
            ept_shipstation_carrier_ids = shipstation_carrier_obj.search(domain)
            if not ept_shipstation_carrier_ids:
                raise UserError("There are no carriers on the shipstation!")
        return ept_shipstation_carrier_ids

    def cron_configuration_action(self):
        """
        Open wizard of "Configure Schedulers" on button click in the instance form view.
        """
        action = self.env.ref('shipstation_ept.action_wizard_shipstation_cron_configuration_ept').read()[0]
        action['context'] = {'default_shipstation_instance_id': self.id}
        return action

    def auto_validate_delivery_order(self, ctx={}):
        """
        Using the cronjob automatic validate the pickings
        """
        instance_id = ctx.get('shipstation_instance_id')
        instance = self.env['shipstation.instance.ept'].browse(instance_id)
        if not instance:
            _logger.info("No Shipstation Instance Found")
            return True
        pickings = self.env['stock.picking'].search(
            [('shipstation_instance_id', '=', instance.id), ('is_exported_to_shipstation', '=', True),
             ('picking_type_id.code', '=', 'outgoing'), ('state', 'not in', ['draft', 'done', 'cancel'])])
        _logger.info("Shipstation delivery orders list for auto validate: %s" % pickings.ids)
        for picking_batch in split_every(10, pickings):
            for picking in picking_batch:
                wiz = picking.with_context(skip_sms=True).button_validate()
                # Immediate Transfer
                if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.immediate.transfer':
                    try:
                        wiz = Form(self.env['stock.immediate.transfer'].with_context(wiz['context'])).save()
                        wiz = wiz.process()
                    except Exception as exception:
                        _logger.info("stock.immediate.transfer : Error {} comes at the time of "
                                     "creating back order in picking : {}".format(exception, picking.id))
                        continue

                # Create Backorder
                if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.backorder.confirmation':
                    try:
                        wiz = Form(self.env['stock.backorder.confirmation'].with_context(wiz['context'])).save()
                        wiz.process()
                        _logger.info("Shipstation backorder created from picking: %s" % picking.id)
                    except Exception as exception:
                        _logger.info("stock.backorder.confirmation : Error {} comes at the time of "
                                     "creating back order in picking : {}".format(exception, picking.id))
                        continue
                picking.find_outgoing_pickings_of_sale_order_and_export_to_shipstation()
                _logger.info("Shipstation delivery order process completed for auto validate: %s" % picking.id)
            self._cr.commit()

    def is_shipstation_instance_exist(self):
        if self.shipstation_api_key and self.shipstation_api_secret_key and self.with_context(active_test=False).search(
                [('shipstation_api_key', '=', self.shipstation_api_key),
                 ('shipstation_api_secret_key', '=', self.shipstation_api_secret_key),
                 ('id', '!=', self.id), ('company_id', '=', self.company_id.id)]):
            raise UserError('Active instance with the given credentials already exist. \n'
                            'Please see archived instance also')

    def write(self, vals):
        res = super(ShipstationInstanceEpt, self).write(vals)
        if vals.get('shipstation_api_key') or vals.get('shipstation_api_secret_key'):
            for rec in self:
                rec.is_shipstation_instance_exist()
                rec.test_shipstation_connection()
                rec.onchange_shipstation_weight_uom()
        return res

    @api.onchange('shipstation_weight_uom')
    def onchange_shipstation_weight_uom(self):
        self.env['shipstation.weight.mapping'].auto_shipstation_weight_mapping()
        for rec in self:
            if rec.shipstation_weight_uom:
                mapping_rec = self.env["shipstation.weight.mapping"].search(
                    [('shipstation_weight_uom', '=', rec.shipstation_weight_uom)], limit=1)
            if not mapping_rec:
                raise UserError(
                    "No weight mapping found for {}, Please define first!!!".format(rec.shipstation_weight_uom))
            rec.weight_uom_id = mapping_rec.shipstation_weight_uom_id.id

    def get_connection(self, url, data=None, params=None, method="GET"):
        """
        Common method to Call the api for shipstation.
        @param url: API url
        @param data: post data for request
        @param params: querystring for request
        @param method: Method of request GET/POST
        @return: content : json data response
        response : Full response
        """
        base64string = base64.encodebytes(
            ('%s:%s' % (self.shipstation_api_key, self.shipstation_api_secret_key)).encode()).decode().replace('\n', '')
        headers = {
            'Authorization': "Basic " + base64string,
            'Content-Type': 'application/json'
        }
        api_url = self.shipstation_url + url
        if self.active_debug_mode:
            _logger.info("ShipStation : {} Request Data : {}".format(api_url, data))
        response = requests.request(method, api_url, headers=headers, data=json.dumps(data), params=params)
        if self.active_debug_mode:
            try:
                _logger.info("ShipStation : {} Response Data : {}".format(api_url, response.json()))
            except:
                _logger.info("ShipStation : {} Response Code : {}".format(api_url, response))
        content = False
        if response.status_code == 200:
            content = response.json()
        return content, response

