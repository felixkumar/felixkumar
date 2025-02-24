#coding: utf-8

from odoo import fields, models


class appointment_contact_info(models.AbstractModel):
    """
    Overwrite to:
    * add type: we CAN NOT rely upon business.resource.type since in the backend reservation it possible to select 
      multiple resource types
    """
    _inherit = "appointment.contact.info"

    dummy_type_id = fields.Many2one("custom.dummy.type")

    def _return_appointment_values(self, pure_values=False, tosession=False):
        """
        Re-write to add custom fields for the vals

        Returns:
         * dict

        Extra info:
         * Expected singleton
        """
        self = self.sudo()
        vals = super(appointment_contact_info, self)._return_appointment_values(pure_values=pure_values)
        if tosession and not self.env["custom.appointment.contact.info.field"]._portal_object_name:
            # hack to avoid dependence issue over custom fields for website
            return vals
        custom_field_ids = self.env["custom.appointment.contact.info.field"].search([])
        if custom_field_ids:
            normal_field_ids = custom_field_ids.filtered(
                lambda fie: fie.ttype not in ["binary"] and fie.field_id.name and hasattr(self, fie.field_id.name)
            )
            all_fields = normal_field_ids and normal_field_ids.mapped("field_id.name") or []
            vals.update(self.read(all_fields, load=False)[0])
            binary_field_ids = custom_field_ids.filtered(
                lambda fie: fie.ttype in ["binary"] and fie.field_id.name and hasattr(self, fie.field_id.name)
            )
            for binary_field in binary_field_ids:
                if self[binary_field.field_id.name]:
                    if pure_values:
                        vals.update({
                            binary_field.field_id.name: self[binary_field.field_id.name],
                            binary_field.field_id.name + "_filename": self[binary_field.field_id.name + "_filename"],
                        })
                    else:
                        vals.update({binary_field.field_id.name: self[binary_field.field_id.name + "_filename"]})
        return vals

    def _return_custom_fields(self, type_id=None):
        """
        The method to return fields which should be mandatory fields (on website!) and also date(time) fields
        Mainly designed for inheritance and for custom fields usage

        Args:
         * type_id - chosen resource type if any        

        Methods:
         * _get_field_names

        Returns:
         * list of chars - of all required field names
         * list of chars - of all date and datetime field names
         * list of chars - of all binary fields
         * list of chars - of all boolean fields
         * list of chars - of all many2one fields

        Extra info:
         * Expected singleton
        """
        self = self.sudo()
        rtype_id = type_id.sudo() or self.env["business.resource.type"] 
        custom_field_ids = self.env["custom.appointment.contact.info.field"].search([("input_placement", "!=", False)])
        date_fields = []
        mandatory_fields = []
        binary_fields = []
        boolean_fields = []
        many2one_fields = []
        if custom_field_ids:
            mandatory_fields = custom_field_ids.filtered(
                lambda fie: fie.required and (not fie.types_ids or (fie.types_ids & rtype_id))
            )
            mandatory_fields = mandatory_fields and mandatory_fields._get_field_names() or []
            date_fields = custom_field_ids._get_field_names(["datetime", "date"])
            binary_fields = custom_field_ids._get_field_names(["binary"])
            boolean_fields = custom_field_ids._get_field_names(["boolean"])
            many2one_fields = custom_field_ids._get_field_names(["many2one"])
        return mandatory_fields, date_fields, binary_fields, boolean_fields, many2one_fields
