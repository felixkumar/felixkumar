from odoo import fields,models,api,_
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"
    
    rate_margin = fields.Integer(string="Margin Percentage (%)")
