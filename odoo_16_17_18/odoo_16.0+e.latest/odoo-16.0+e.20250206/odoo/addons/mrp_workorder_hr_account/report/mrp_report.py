# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class MrpReport(models.Model):
    _inherit = "mrp.report"

    def _op_cost_query(self):
        # Method overridden to compute employee cost
        # In this query is added to calculate cost based on both workcenter costs and employee costs
        return """
            WITH op_employee_costs AS (
                SELECT SUM(t.employee_cost / 60. * t.duration) AS op_employee_cost, mo.id AS mo_id
                FROM mrp_production AS mo
                LEFT JOIN mrp_workorder wo ON mo.id = wo.production_id
                LEFT JOIN mrp_workcenter_productivity t ON t.workorder_id = wo.id
                WHERE t.workorder_id = wo.id
                GROUP BY mo.id
            )
            SELECT
                mo_id                                                                    AS mo_id,
                SUM(op_costs_hour / 60. * op_duration) + op_employee_cost_total          AS total,
                SUM(op_duration)                                                         AS total_duration
            FROM (
                SELECT
                    mo.id AS mo_id,
                    CASE
                        WHEN wo.costs_hour != 0.0 AND wo.costs_hour IS NOT NULL THEN wo.costs_hour
                        ELSE COALESCE(wc.costs_hour, 0.0) END                                       AS op_costs_hour,
                    COALESCE(SUM(wo.duration), 0.0)                                                 AS op_duration,
                    COALESCE(oec.op_employee_cost, 0.0)                                             AS op_employee_cost_total
                FROM mrp_production AS mo
                LEFT JOIN mrp_workorder wo ON wo.production_id = mo.id
                LEFT JOIN mrp_workcenter wc ON wc.id = wo.workcenter_id
                LEFT JOIN op_employee_costs oec ON oec.mo_id = mo.id
                WHERE mo.state = 'done'
                GROUP BY
                    mo.id,
                    wc.costs_hour,
                    wo.id,
                    COALESCE(oec.op_employee_cost, 0.0)
                ) AS op_cost_vars
            GROUP BY mo_id, op_employee_cost_total
        """
