from odoo import models, fields


class EDEnvironment(models.Model):
    _name = 'edi.environment'
    _description = 'Edi Environment'

    name = fields.Char(string="Name")
    mode = fields.Selection([('enable', 'Enable'),
                             ('disable', 'Disable'),
                             ('testing', 'Testing')],
                            string='Mode')
