# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class custom_fields_prepare_selection(models.TransientModel):
    """
    The wizard to apply field selection values based on comma-separated lists of new values
    """
    _name = "custom.fields.prepare.selection"
    _description = "Add comma-separated selection values"

    res_model = fields.Char("Resource Model")
    res_id = fields.Integer("Resource ID")
    selection_values = fields.Char(string="New values", required=True)

    def action_prepare_selection_values(self):
        """
        The method to open new article form with structured from template description

        Extra info:
         * Expected singleton
        """
        field_id = self.env[self.res_model].browse(self.res_id)
        if field_id.exists():
            try:
                new_values_list = self.selection_values.split(",")
                new_vals = []
                for new_value in new_values_list:
                    new_vals.append((0, 0, {"value": new_value}))
                field_id.write({"sel_options_ids": new_vals})
            except Exception as e:
                raise UserError(_("New values should be a comma separated string!"))
