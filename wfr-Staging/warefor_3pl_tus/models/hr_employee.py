from odoo import models, fields, api


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    partner_id = fields.Many2one('res.partner', string='Partner')
    building = fields.Char(string='Building')
    start_date = fields.Date(string='Start date')

