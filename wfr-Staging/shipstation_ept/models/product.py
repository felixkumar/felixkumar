import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def create_shipstation_product(self):
        """
        to create product records in the shipstation layer
        @return:
        """
        shipstation_product_obj = self.env['shipstation.product.ept']

        model_id = self.env['ir.model'].sudo().search([('model', '=', self._name)]).id
        log_line = self.env['common.log.lines.ept']

        instance = self.env['shipstation.instance.ept'].search([('company_id', '=', self.env.company.id)], limit=1)
        if not instance:
            message = "Shipstation instance not found for company {}..".format(self.env.company.name)
            log_line.create_common_log_line_ept(message=message, model_id=model_id, operation_type='export',
                                                module='shipstation_ept', log_line_type='fail')
            return True
        _logger.info('Shipstation product create for instance %s', instance.name)

        for product in self:
            _logger.info('creating shipstation product for product: %s', product.id)
            try:
                self.create_product(shipstation_product_obj, product, instance, model_id, log_line)
                continue
            except Exception as exception:
                msg = "Error while creating shipstation product for {}. error: {}".format(product.id, exception)
                _logger.info(msg)
                log_line.create_common_log_line_ept(message=msg, model_id=model_id, operation_type='export',
                                                    module='shipstation_ept', log_line_type='fail')
                continue

    def create_product(self, shipstation_product_obj, product, instance, model_id, log_line):
        existing_shipstation_product = shipstation_product_obj.search(
            [('shipstation_sku', '=', product.default_code), ('shipstation_instance_id', '=', instance.id)])
        if existing_shipstation_product:
            message = ("Shipstation product already exist! Product : %s" % product.id)
            log_line.create_common_log_line_ept(message=message, model_id=model_id, operation_type='export',
                                                module='shipstation_ept', log_line_type='fail')
        shipstation_product_obj.create({
            'name': product.name,
            'product_id': product.id,
            'shipstation_identification': "",
            'shipstation_sku': product.default_code,
            'shipstation_instance_id': instance.id,
            'height': 0,
            'width': 0,
            'length': 0,
            'weight': self.env.company.get_weight_uom_id()._compute_quantity(
                product.weight,
                self.env.ref(
                    "uom.product_uom_oz"))
        })
        log_line.create_common_log_line_ept(message="Shipstation product created in odoo.",
                                            model_id=model_id, operation_type='export',
                                            module='shipstation_ept', log_line_type='success',
                                            res_id=shipstation_product_obj.id)
