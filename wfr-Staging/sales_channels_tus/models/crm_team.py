from odoo import api, fields, models, _


class CrmTeamInherit(models.Model):
    _inherit = "crm.team"

    sales_channel_id = fields.Many2one('sales.channel', string='Sales Channel')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")