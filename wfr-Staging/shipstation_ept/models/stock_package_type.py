from odoo import fields, models, api


class StockPackageType(models.Model):
    _inherit = 'stock.package.type'

    package_carrier_type = fields.Selection(selection_add=[('shipstation_ept', 'Shipstation')],
                                            ondelete={'shipstation_ept': 'cascade'})
    ept_shipstation_carrier_id = fields.Many2one('shipstation.carrier.ept',
                                             string='Shipstation Carrier')
    shipstation_instance_id = fields.Many2one('shipstation.instance.ept',
                                              string='Shipstation Instance')

    @api.model
    def create(self, vals):
        """
        Add: override create method of stock.package.type
        @param vals: record of stock.package.type
        @return: returns the value of stock.package.type
        """
        if vals.get('ept_shipstation_carrier_id', False):
            current_carrier_id = self.env["shipstation.carrier.ept"].browse(vals.get('ept_shipstation_carrier_id'))
            vals.update({
                "shipstation_instance_id": current_carrier_id.shipstation_instance_id.id,
                "company_id": current_carrier_id.company_id.id,
                "package_carrier_type": 'shipstation_ept'
            })
        return super(StockPackageType, self).create(vals)
