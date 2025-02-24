from odoo import fields, models


class L10nRoSaftTaxType(models.Model):
    _name = 'l10n_ro_saft.tax.type'
    _description = 'Romanian SAF-T Tax Type'
    _rec_names_search = ['code', 'description']

    code = fields.Char('Code', required=True)
    description = fields.Char('Description', required=True, translate=True)

    _sql_constraints = [
        ('code_unique', 'unique (code)', 'The code of the tax type must be unique !'),
    ]

    def name_get(self):
        return [(tax_type.id, f'{tax_type.code} {tax_type.description}') for tax_type in self]
