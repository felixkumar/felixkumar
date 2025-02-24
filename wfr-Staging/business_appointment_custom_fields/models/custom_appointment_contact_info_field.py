# -*- coding: utf-8 -*-

from odoo import api, fields, models


class custom_appointment_contact_info_field(models.Model):
    """
    Overwrite to introduce appointment info fields
    """
    _name = "custom.appointment.contact.info.field"
    _inherit = ["custom.extra.field"]
    _description = "Custom Appointment Field"
    _field_code = "cbaf"
    _linked_model = "appointment.contact.info"
    _type_field = "resource_type_id"
    _type_field_model = "business.resource.type"
    _backend_views = [
        "business_appointment_custom_fields.business_appointment_core_view_form",
        "business_appointment_custom_fields.business_appointment_view_form",
        "business_appointment_custom_fields.choose_appointment_customert_form_view",
    ]
    _other_model_fields = ["business.appointment.core", "business.appointment", "choose.appointment.customer"]

    def _inverse_active(self):
        """
        Overwritting to remove report fields (to avoid excess data)
        """
        super(custom_appointment_contact_info_field, self)._inverse_active()
        for field in self:
            if not field.active:
                field.used_in_report = False

    def _inverse_ttype(self):
        """
        Overwritting to manage setting of report based on ttype
        """
        super(custom_appointment_contact_info_field, self)._inverse_ttype()
        for field in self:
            if field.ttype in ["text", "html", "binary"]:
                field.used_in_report = False

    types_ids = fields.Many2many(
        "business.resource.type",
        "business_resource_type_field_reservations_reltable",
        "business_resource_type_rel_id",
        "custom_reservation_field_rel_id",
        string="Types",
        help="Leave it empty, if this field should appear for all resources disregarding type",
    )
    placement = fields.Selection(
        selection_add=[
            ("left_panel_group", "Left Column"),
            ("right_panel_group", "Rigth Column"),
            ("after_description_group", "After Description"),
        ],
    )
    sel_options_ids = fields.One2many(context={"default_model": "custom.appointment.contact.info.field"},)
    linked_field_ids = fields.Many2many(
        "ir.model.fields",
        "ir_model_fields_contact_info_custom_rel_table",
        "fields_id",
        "contact_info_custom_field_id",
        string="Related Model Fields",
        copy=False,
    )
    linked_binary_ids = fields.Many2many(
        "ir.model.fields",
        "ir_model_fields_contact_info_finary_rel_table",
        "fields_id",
        "contact_info_custom_field_id",
        string="Related Model Binary Fields",
        copy=False,
    )
    used_in_report = fields.Boolean(string="Used for Analysis",)
    report_field_id = fields.Many2one("ir.model.fields", string="Report Field")
    active = fields.Boolean(inverse=_inverse_active)
    ttype = fields.Selection(inverse=_inverse_ttype)

    def write(self, values):
        """
        Overwrite to keep changes not only in field_id but also in report_field_id

        Extra info:
         * we do not use inverse since it is triggered before create, and report cannot be inited
         * we can safely remove / recover report field, since its data would be recovered during init (kept really
           in business appointment)
        """
        custom_field_id = super(custom_appointment_contact_info_field, self).write(values)
        for field in self:
            if values.get("used_in_report") is not None:
                if field.used_in_report:
                    report_field_id = field.sudo()._prepare_new_report_field()
                    field.report_field_id = report_field_id                       
                if not field.used_in_report and field.report_field_id:
                    field.report_field_id.sudo().unlink()
            if field.report_field_id:
                new_field_values = field.sudo()._return_new_field_values()
                field.report_field_id.sudo().write(new_field_values)
        return custom_field_id

    @api.model_create_multi
    def create(self, vals_list):
        """
        Re-write to pass report_field creation

        Methods:
         * _prepare_new_report_field
        """
        custom_field_ids = super(custom_appointment_contact_info_field, self).create(vals_list)
        for custom_field_id in custom_field_ids:
            if custom_field_id.used_in_report:
                report_field_id = custom_field_id.sudo()._prepare_new_report_field()
                custom_field_id.report_field_id = report_field_id
        return custom_field_ids

    def unlink(self):
        """
        Fully re-write to unlink also all fields of related models and report fields
        """
        field_to_remove =self.mapped("linked_field_ids") + self.mapped("linked_binary_ids") \
            + self.mapped("report_field_id")
        custom_field_id = super(custom_appointment_contact_info_field, self).unlink()
        self.sudo()._generate_xml()
        field_to_remove.sudo().unlink()

    @api.model
    def _generate_xml(self, clean_xml=False):
        """
        Re-write to firstly prepare fields for linked models (we do this check always for all fields)
        """
        if not self._context.get("noxml_ba_update"):
            self.sudo()._update_related_model_fields()
            return super(custom_appointment_contact_info_field, self)._generate_xml(clean_xml=clean_xml)

    @api.model
    def _update_related_model_fields(self):
        """
        The method to create / update fields in related models

        Methods:
         * _return_new_field_values
        """
        all_fields = self.search([])
        for field in all_fields:
            field_id = field.field_id
            binary_field_id = field.binary_field_id
            if field_id:
                all_related_field_ids = field.linked_field_ids.mapped("model")
                # create new fields 
                to_create_fields = list(set(self._other_model_fields) - set(all_related_field_ids))
                for related_field in to_create_fields:
                    new_field = field_id.copy(default={
                        "model": related_field, "model_id": self.env["ir.model"]._get_id(related_field),
                    })
                    field.with_context(noxml_ba_update=True).linked_field_ids = [(4, new_field.id)]
                # write in existing
                to_write_fields = list(set(self._other_model_fields) - set(to_create_fields))
                if to_write_fields:
                    to_wite_field_ids = field.linked_field_ids.filtered(lambda fie: fie.model in to_write_fields)
                    new_field_values = field._return_new_field_values()
                    to_wite_field_ids.write(new_field_values)
            if binary_field_id:
                all_related_binary_ids = field.linked_binary_ids.mapped("model_id.model")
                for related_field in self._other_model_fields:
                    if related_field not in all_related_binary_ids:
                        # need to be created only
                        new_field = binary_field_id.copy(default={
                            "model": related_field, "model_id": self.env["ir.model"]._get_id(related_field),
                        })
                        field.with_context(noxml_ba_update=True).linked_binary_ids = [(4, new_field.id)]

    def _get_field_names(self, field_types=[]):
        """
        The method to return all website custom input fields of the certatin type

        Args:
         * field type - list of char, e.g. ["datetime", "date"]
       
        Returns:
         * list of char
        """
        if field_types:
            cfields = field_types and self.filtered(lambda fie: fie.ttype in field_types)
        else:
            cfields = self
        fields_names = cfields and cfields.mapped("field_id.name") or []
        return fields_names

    def _prepare_new_report_field(self):
        """
        The method to create a new ir.models.field of appointment.analytic
        We can't use standard method since the model is different

        Methods:
         * _return_new_field_values()
         * _get_id of ir.model

        Returns:
         * ir.models.field object

        Extra info:
         * Expected singleton
        """
        field_values = self._return_new_field_values()
        field_unique_name = "x_oz_{}_report_{}".format(self._field_code, self.id)
        core_name = field_unique_name
        itera = 0
        while self.env["ir.model.fields"].sudo()._search([("name", "=", field_unique_name)], limit=1):
            field_unique_name = "{}_{}".format(core_name, itera)
            itera += 1
        field_values.update({
            "name": field_unique_name,
            "model_id": self.env["ir.model"].sudo()._get_id("appointment.analytic"),
            "ttype": self.ttype,
            "copied": True,
            "relation": self.ttype in ["many2one"] and self.res_model or False,
        })
        field_id = self.env["ir.model.fields"].sudo().create(field_values)
        return field_id
