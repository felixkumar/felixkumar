# -*- coding: utf-8 -*-

from odoo import api, fields, models


class business_appointment_custom_search(models.Model):
    """
    The model to keep custom search values for portal
    """
    _name = "business.appointment.custom.search"
    _description = "Custom Search"

    @api.onchange("custom_field_id")
    def _onhcnage_custom_field_id(self):
        """
        Onchnage method for custom_field_id
        """
        for csearch in self:
            csearch.name = csearch.custom_field_id.field_description

    custom_field_id = fields.Many2one("ir.model.fields", string="Field", required=True, ondelete="cascade")
    name = fields.Char("Label", required=True, translate=True)
    model = fields.Char(string="Model")
