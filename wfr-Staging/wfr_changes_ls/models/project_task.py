from odoo import fields, models, api


class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    dev_description = fields.Html(string=' Developer Notes', sanitize_attributes=False)
