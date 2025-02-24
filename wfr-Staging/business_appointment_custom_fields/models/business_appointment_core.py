#coding: utf-8

from odoo import models


class business_appointment_core(models.Model):
    """
    Overwrite to guarantee vals to pass in business logic
    """
    _inherit = "business.appointment.core"

    def _prepare_vals_for_real_appointment_prereserv(self):
        """
        Re-wrtie to add custom fields

        Returns:
         * dict
        """    
        vals = super(business_appointment_core, self)._prepare_vals_for_real_appointment_prereserv()
        self = self.sudo()
        custom_fields = self.env["custom.appointment.contact.info.field"].search([])
        if custom_fields:
            custom_fields_labels = custom_fields.mapped("field_id.name") + custom_fields.mapped("binary_field_id.name")
            new_vals = self.read(fields=custom_fields_labels, load=False)[0]
            if new_vals.get("id"):
                del new_vals["id"]
            vals.update(new_vals)
        return vals

