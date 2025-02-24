from odoo import models, fields


class RacksConfiguration(models.Model):
    _name = 'racks.configuration'
    _description = 'Configuration For Racks'

    name = fields.Char(string="Name")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    limit = fields.Integer(string="Limit")
    row = fields.Integer(string="Row")
    column = fields.Integer(string="Column")
    column_space = fields.Integer(string="Space Between Column")
    row_space = fields.Integer(string="Space Between Row")
    rack_space = fields.Integer(string="Space Between Rack")
    starting_position_x = fields.Integer(string='Starting Position (X)')
    starting_position_y = fields.Integer(string='Starting Position (Y)')
    starting_position_z = fields.Integer(string='Starting Position (Z)')
    size_x = fields.Integer(string="Size(X)")
    size_y = fields.Integer(string="Size(Y)")
    size_z = fields.Integer(string="Size(Z)")
    toggle_row = fields.Boolean(string="Toggle Row")
    toggle_column = fields.Boolean(string="Toggle Column")

    _sql_constraints = [
        ('warehouse_id', 'unique(warehouse_id)',
         'Warehouse must be unique.')
    ]
