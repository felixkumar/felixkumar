# -*- coding: utf-8 -*-

from odoo import models


class appointment_analytic(models.Model):
    """
    Overwrite to add custom fields
    """
    _inherit = "appointment.analytic"

    def _return_custom_fields(self):
        """
        The method to return all custom fields

        Returns:
         * tuple: string, string
        """
        custom_fields_query = """
            SELECT ir.name,
                   irr.name 
            FROM "custom_appointment_contact_info_field" c
                LEFT JOIN ir_model_fields ir ON (c.field_id=ir.id)
                LEFT JOIN ir_model_fields irr ON (c.report_field_id=irr.id)
            WHERE COALESCE(report_field_id, 0) != 0 
                  AND COALESCE(field_id, 0) != 0
                  AND used_in_report = TRUE 
                  AND active = TRUE
            GROUP BY ir.name, irr.name"""
        self._cr.execute(custom_fields_query)
        custom_fields = self._cr.fetchall()    
        select_str = groupby_str = ""
        for field in custom_fields:
            select_str += """,
                a.{} as {}""".format(field[0], field[1])
            groupby_str += """,
                a.{}""".format(field[0])
        return (select_str, groupby_str)

    def _select_query(self):
        """
        Overwrite to add custom fields

        Methods:
         * _return_custom_fields
        """
        return super(appointment_analytic, self)._select_query() + self._return_custom_fields()[0]

    def _group_by_query(self):
        """
        Overwrite to add custom fields

        Methods:
         * _return_custom_fields
        """
        return super(appointment_analytic, self)._group_by_query() + self._return_custom_fields()[1]
