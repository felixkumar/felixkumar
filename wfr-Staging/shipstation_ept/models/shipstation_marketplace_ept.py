from odoo import models, fields


class ShipstationMarketplace(models.Model):
    """
    Class for Shipstation Marketplaces.
    """
    _name = 'shipstation.marketplace.ept'
    _description = 'Shipstation Marketplace'

    name = fields.Char(string='Name')
    shipstation_identification = fields.Integer(string='Marketplace Id')
    shipstation_instance_id = fields.Many2one('shipstation.instance.ept', string='Instance', ondelete='cascade')
    active = fields.Boolean('Active',
                            help="If the active field is set to False, then "
                                 "can not access the Marketplace.",
                            default=True)
    company_id = fields.Many2one(related='shipstation_instance_id.company_id', store=True, string='Company')
