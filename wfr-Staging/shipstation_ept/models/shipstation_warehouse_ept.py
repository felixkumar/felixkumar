from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ShipstationWarehouse(models.Model):
    """
    Model for shipstation warehouses.
    """
    _name = 'shipstation.warehouse.ept'
    _description = 'Shipstation Warehouse'

    shipstation_instance_id = fields.Many2one('shipstation.instance.ept', string='Instance', ondelete='cascade')
    name = fields.Char(string='Name')
    is_default = fields.Boolean(string='Is Default')
    shipstation_identification = fields.Integer(string='ShipStation Warehouse')
    origin_address_id = fields.Many2one('res.partner', string="Origin Address")
    return_address_id = fields.Many2one('res.partner', string="Return Address")
    odoo_warehouse_id = fields.Many2one('stock.warehouse')
    active = fields.Boolean('Active', default=True,
                            help="If the active field is set to False, then can not access the Shipstation Warehouse.")
    company_id = fields.Many2one(related='shipstation_instance_id.company_id', store=True, string='Company')

    @api.constrains('is_default')
    def _check_warehouse_is_default(self):
        if self.is_default:
            if self.search([('shipstation_instance_id', '=', self.shipstation_instance_id.id),
                            ('is_default', '=', True), ('id', '!=', self.id)]):
                raise ValidationError("There is an shipstation warehouse set as default in system.")
