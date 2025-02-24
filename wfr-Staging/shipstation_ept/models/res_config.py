
from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    shipstation_instance_id = fields.Many2one("shipstation.instance.ept", string="Shipstation Instance")
    tracking_link = fields.Char(string="Tracking Link",
                                help="Tracking link(URL) useful to track the "
                                     "shipment or package from this URL.",
                                size=256)
    shipstation_weight_uom = fields.Selection([('grams', 'Grams'),
                                               ('pounds', 'Pounds'),
                                               ('ounces', 'Ounces')], default='grams',
                                              string="Supported Weight UoM",
                                              help="Supported Weight UoM by ShipStation")
    shipstation_package_id = fields.Many2one('stock.package.type', string='Shipstation Package')
    shipstation_last_export_order = fields.Datetime(string='Last Export Order')
    last_import_product = fields.Datetime(string='Last Sync Product')
    active_debug_mode = fields.Boolean(string='Active Debug Mode', copy=False, default=False)
    
    @api.onchange('shipstation_instance_id')
    def onchange_shipstation_instance_id(self):
        vals = {}
        if self.shipstation_instance_id:
            instance_id = self.shipstation_instance_id
            vals['tracking_link'] = instance_id.tracking_link or False
            vals['shipstation_weight_uom'] = instance_id.shipstation_weight_uom or False
            vals['active_debug_mode'] = instance_id.active_debug_mode or False
        return {'value': vals}
    
    def execute(self):
        instance_id = self.shipstation_instance_id
        values = {}
        res = super().execute()
        ctx = {}
        if instance_id:
            ctx.update({'default_instance_id': instance_id.id})
            values['tracking_link'] = self.tracking_link or False
            values['shipstation_weight_uom'] = self.shipstation_weight_uom or False
            values['active_debug_mode'] = self.active_debug_mode or False

            mapping_rec = self.env["shipstation.weight.mapping"].search(
                [('shipstation_weight_uom', '=', self.shipstation_weight_uom)], limit=1)
            if mapping_rec:
                values['weight_uom_id'] = mapping_rec.shipstation_weight_uom_id.id or False

            instance_id.sudo().write(values)
        return res
