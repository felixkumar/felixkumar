# -*- coding: utf-8 -*-

from odoo import models

class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_operation_cost(self, duration, operation):
        employee_cost = (duration / 60.0) * operation.workcenter_id.employee_costs_hour * operation.employee_ratio
        return super()._get_operation_cost(duration, operation) + employee_cost
