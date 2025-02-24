# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def write(self, vals):
        origin_analytic_account = {production: production.analytic_account_id for production in self}
        res = super().write(vals)
        for production in self:
            if 'analytic_account_id' in vals and production.state != 'draft':
                if vals['analytic_account_id'] and origin_analytic_account[production]:
                    production.workorder_ids.employee_analytic_account_line_ids.write({'account_id': vals['analytic_account_id']})
                elif vals['analytic_account_id'] and not origin_analytic_account[production]:
                    production.workorder_ids.time_ids._create_analytic_entry()
                else:
                    production.workorder_ids.employee_analytic_account_line_ids.unlink()

        return res
