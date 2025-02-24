# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PalletConfiguration(models.Model):
    _name = 'pallet.configuration'
    _description = 'Pallet configuration'

    name = fields.Char(string="Name")
    width = fields.Float(_('Width'))
    depth = fields.Float(_('Depth'))
    max_height = fields.Float(_('Max Height'))
    weight = fields.Float(_('Weight'))
    cube = fields.Float(_('Cube'), compute="_compute_cube")
    mx_cube_height = fields.Float(_('Max Cube Height'))
    mx_weight = fields.Float(_('Max Weight'))
    description = fields.Text(_("Description"))
    product_id = fields.Many2one(comodel_name="product.product", string="Product")

    @api.depends('width', 'depth', 'max_height')
    def _compute_cube(self):
        for rec in self:
            rec.cube = 0.0
            if rec.width or rec.depth or rec.max_height:
                rec.cube = (rec.width * rec.depth * rec.max_height) / 1728
