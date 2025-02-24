import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ShipstationWeightMapping(models.Model):
    """
    Class for ShipStation Carriers.
    """
    _name = 'shipstation.weight.mapping'
    _description = 'Shipstation Weight Mapping'
    _rec_name = 'shipstation_weight_uom'

    shipstation_weight_uom = fields.Selection([('grams', 'Grams'),
                                               ('pounds', 'Pounds'),
                                               ('ounces', 'Ounces')], default='grams',
                                              string="Supported Weight UoM",
                                              help="Supported Weight UoM by ShipStation")
    shipstation_weight_uom_id = fields.Many2one("uom.uom",
                                                domain=lambda self: [('category_id.id', '=',
                                                                      self.env.ref('uom.product_uom_categ_kgm').id)],
                                                help="This UOM will be used while converting the weight in "
                                                     "different units of measurement. Set Shipping UoM Same as "
                                                     "Supported Weight UoM.")

    @api.constrains('shipstation_weight_uom')
    def _check_details(self):
        for rec in self:
            if self.search([('shipstation_weight_uom', '=', rec.shipstation_weight_uom), ('id', '!=', rec.id)]):
                raise UserError('Shipstation Weight Uom must be unique.')

    def auto_shipstation_weight_mapping(self):
        """
        For automatic weight mapping with shipstation at time of create shipstation instance
        """
        if not self.search([('shipstation_weight_uom', '=', 'grams')]):
            self.create({
                'shipstation_weight_uom': 'grams',
                'shipstation_weight_uom_id': self.env.ref('uom.product_uom_gram').id
            })
        if not self.search([('shipstation_weight_uom', '=', 'pounds')]):
            self.create({
                'shipstation_weight_uom': 'pounds',
                'shipstation_weight_uom_id': self.env.ref('uom.product_uom_lb').id
            })
        if not self.search([('shipstation_weight_uom', '=', 'ounces')]):
            self.create({
                'shipstation_weight_uom': 'ounces',
                'shipstation_weight_uom_id': self.env.ref('uom.product_uom_oz').id
            })
