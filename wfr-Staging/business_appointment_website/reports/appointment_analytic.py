# -*- coding: utf-8 -*-

from odoo import fields, models

class appointment_analytic(models.Model):
    """
    Overwrite to add website-specific options
    """
    _inherit = "appointment.analytic"
    
    website_id = fields.Many2one(
        "website",
        string="Website",
        readonly=True,
    )

    def _select_query(self):
        """
        Overwrite to add website
        """
        return super(appointment_analytic, self)._select_query() + """,
                a.website_id""" 
        
    def _group_by_query(self):
        """
        Overwrite to add website
        """
        return super(appointment_analytic, self)._group_by_query() + """,
                a.website_id"""
