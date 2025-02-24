from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CrmTeam(models.Model):
    _inherit = 'crm.team'
    _check_company_auto = True

    store_id = fields.Many2one('shipstation.store.ept', string="ShipStation Store", company_dependent=True,
                               help="It is dependent on company of sales team and carrier.", tracking=True)
    delivery_carrier_id = fields.Many2one('delivery.carrier',
                                          string="Default Delivery Carrier",
                                          help="If sale order has no Carrier selected, Carrier selected here will "
                                               "be set to the sale order which is having this Sales Team.",
                                          company_dependent=True, tracking=True)
    export_order = fields.Boolean(string='Export order to ShipStation?')
    shipstation_update_carrier = fields.Boolean("Update Carrier Based on ShipStation Shipments?", tracking=True,
                                                help="Odoo update the carrier of picking at the time of updating "
                                                     "tracking number from shipstation")

    @api.onchange('delivery_carrier_id')
    def onchange_carrier_id(self):
        """This method will sets the store_id on change deliver_carrier"""
        return {'domain': {
            'store_id': self.delivery_carrier_id.id and
                        [('shipstation_instance_id', '=', self.delivery_carrier_id.shipstation_instance_id.id)]}}

    @api.onchange('store_id')
    def onchange_store_id(self):
        """This method sets the delivery_carrier onchange store_id"""
        return {'domain': {
            'delivery_carrier_id': self.store_id.id and
                                   [('shipstation_instance_id', '=', self.store_id.shipstation_instance_id.id)]}}

    @api.constrains('delivery_carrier_id', 'store_id')
    def _check_details(self):
        """This method will checks the details of the shipstation
        based on store and delivery carrier"""
        if self.store_id and self.delivery_carrier_id and \
                self.store_id.shipstation_instance_id != self.delivery_carrier_id.shipstation_instance_id:
            raise ValidationError(_('ShipStation Store and delivery carrier should be from same Shipstation instance.'))
