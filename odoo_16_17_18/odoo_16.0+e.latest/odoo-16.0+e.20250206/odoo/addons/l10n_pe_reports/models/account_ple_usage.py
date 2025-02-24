from odoo import fields, models


class L10nPEPleUsage(models.Model):
    _name = "l10n_pe.ple.usage"
    _description = "Service that is reflected in the declared invoice and must be classified according to table 31, used on purchase report 8.2"
    _rec_names_search = ["name", "code"]

    code = fields.Char(required=True, help="Value to be used in the purchase report.")
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    def name_get(self):
        result = []
        for prod in self:
            result.append((prod.id, "%s %s" % (prod.code, prod.name or "")))
        return result
