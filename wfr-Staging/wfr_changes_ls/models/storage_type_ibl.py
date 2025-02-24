from odoo import fields, models


class StorageTypeIBL(models.Model):
    _inherit = 'storage.type.ibl'
    _order = 'sequence'

    sequence = fields.Integer("Sequence")
