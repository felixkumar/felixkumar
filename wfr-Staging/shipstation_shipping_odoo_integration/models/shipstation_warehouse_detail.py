from odoo import models, fields, api
import datetime


class ShipstationWarehouseDetail(models.Model):
    _name = "shipstation.warehouse.detail"
    _description = "Shipstation Warehouse Detail"
    _order = 'id desc'
    _inherit = ['mail.thread']
    
    name = fields.Char(string='Warehouse name')
    warehouse_id = fields.Char(string='Warehuse Id')
    shipstation_configuration_id = fields.Many2one('shipstation.odoo.configuration.vts', string='Shipstation Configuration')

