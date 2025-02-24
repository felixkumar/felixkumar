import base64

from odoo import fields, models

class XmlXsdImport(models.TransientModel):
    _name = 'xml.xsd.import'
    _description = 'Wizard to import XML XSD'

    name = fields.Char(string='Name')
    file = fields.Binary(string='File')

    def action_create_xsd(self):
        res = self.env['xml.xsd']
        for wizard in self:
            res |= self.env['xml.xsd'].create_from_xsd(wizard.name, base64.b64decode(wizard.file))
        if len(res) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'xml.xsd',
                'res_id': res.id,
                'view_mode': 'form',
            }
        elif len(res) > 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'xml.xsd',
                'domain': [('id', 'in', res._ids)],
                'view_mode': 'tree,form',
            }
