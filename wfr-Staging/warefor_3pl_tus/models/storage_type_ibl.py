from odoo import api, fields, models

class StorageTypeIbl(models.Model):
    _name = 'storage.type.ibl'
    _description = 'Storage Type IBL'

    name = fields.Char(string='Storage Type')
