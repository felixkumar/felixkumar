from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class XmlXsdLine(models.Model):
    _inherit = 'xml.xsd.line'

    is_trading_partner_field = fields.Boolean(string='Is Trading Partner Id Tag')

    @api.constrains('is_trading_partner_field')
    def _check_max_one_trading_partner_field_per_xsd(self):
        for line in self:
            if len(line.xsd_id.xsd_line_ids.filtered('is_trading_partner_field')) > 1:
                raise ValidationError(_('Each XSD can only have one Trading Partner Id Tag'))
