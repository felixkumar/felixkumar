# -*- coding: utf-8 -*-

from lxml import etree
from lxml.builder import E

from odoo import api, fields, models

FIELDS_INPUTS_REL = {
    "char": "text", "integer": "number", "float": "number", "boolean": "checkbox", "date": "date", "datetime": "date", 
    "binary": "file",
}


class custom_appointment_contact_info_field(models.Model):
    """
    Inherit to add fields for all contact.info related objects: contact.info, business.appointment.core, 
    business.appointment
    """
    _inherit = "custom.appointment.contact.info.field"
    _portal_object_name = "ba_appointment_id"
    _portal_views = ["business_appointment_custom_fields_website.portal_appointment_page_custom"]
    _input_views = ["business_appointment_custom_fields_website.ba_contact_info"]
    _other_model_fields = ["business.appointment.core", "business.appointment", "choose.appointment.customer",
        "website.business.appointment"]

    portal_placement = fields.Selection(
        selection_add=[("left_panel_group", "Left Column"),("right_panel_group", "Rigth Column"),]
    )

    @api.model
    def _prepare_custom_view(self, view, xml_content):
        """
        Re-write to hack web/content routes
        """
        super(custom_appointment_contact_info_field, self)._prepare_custom_view(view=view, xml_content=xml_content)
        custom_view_key = u"{}_xoz".format(view.id)
        custom_view = self.env["ir.ui.view"].search([("key", "=", custom_view_key)], limit=1)    
        if custom_view:
            custom_view.arch = custom_view.arch.replace("appointment.contact.info", "business.appointment")

    @api.model
    def _prepare_input_view_xml(self, clean_xml=False):
        """
        Fully re-write to add proper classes and default values

        Methods:

         * _return_input_elememt
         * formbuilder_whitelist of ir.model.fields
         * _prepare_custom_view

        Args:
         * clean_xml: Boolean - to clean xml of custom fields disregarding their existance
        """
        all_views = self._get_all_views(self._input_views)
        for view in all_views:
            custom_field_ids = clean_xml and self.env[self._name] \
                or self.env[self._name].search([("input_placement", "!=", False)])
            whitelist_fields = custom_field_ids.mapped("field_id.name")
            self.env["ir.model.fields"].formbuilder_whitelist(self._linked_model, whitelist_fields)
            placement_ids = dict(self._fields["input_placement"].selection).keys()
            xml_content = ""
            for place in placement_ids:
                final_xml = []
                for customom_field in custom_field_ids:
                    if customom_field.input_placement == place and customom_field.ttype not in ["datetime"]:
                        required_to_fill = (customom_field.required and customom_field.ttype not in ["boolean"]) \
                            and True or False 
                        field_name = customom_field.field_id and customom_field.field_id.name or False
                        if field_name:
                            inner_xml = []
                            label_attrs = {
                                "class":  required_to_fill and "col-form-label" or "col-form-label label-optional", 
                                "for": field_name,
                            }
                            inner_xml.append(E.label(customom_field.name, label_attrs))
                            inner_xml += customom_field._return_input_elememt(field_name)
                            OUTERDIVCLASS = "form-group #{" \
                                + "error.get('{}') and 'o_has_error'  or ''".format(field_name) \
                                + "} col-xl-6 type_visibility_depend"
                            final_xml.append(E.div(*(inner_xml), {"t-attf-class": OUTERDIVCLASS}))

                xml = E.t(E.t(*(final_xml), id=place), id=place, position="replace",)
                xml_content += etree.tostring(xml, pretty_print=False, encoding="unicode")
            self._prepare_custom_view(view, xml_content)

    def _return_input_elememt(self, field_name):
        """
        Re-write to have own logic for fields (classes and values)

        Args:
          * field_name - name of ir.model.field

        Returns:
         * list of xml --> should be just xml tag
        """
        div_inner_xml = []
        input_attrs = {
            "t-attf-class": "s_website_form_input form-control #{" + "error.get('{}') and 'is-invalid' or ''".format(
                field_name
            ) +"}",
            "name": field_name,
            "type": FIELDS_INPUTS_REL.get(self.ttype) or FIELDS_INPUTS_REL.get("char"),
        }
        if self.types_ids:
            invisible = "{}".format(",".join(map(str, self.types_ids.ids)),)
            input_attrs.update({"invisible": invisible})
        if self.ttype in ["char", "integer", "float", "date", "datetime"]:
            input_attrs.update({"t-att-value": field_name,})
            div_inner_xml.append(E.input("", input_attrs))
        elif self.ttype in ["binary"]:
            loaded_attrs = {
                "t-attf-class": "form-control ba_binary_input #{" + "error.get('{}') and 'is-invalid' or ''".format(
                    field_name) +"}",
                "name": field_name,
                "t-att-value": field_name,
            }
            readonly_input = [E.input("", loaded_attrs)]
            first_binary = E.t(*(readonly_input), {"t-if": field_name})
            div_inner_xml.append(first_binary)  
            input_input = [E.input("", input_attrs)]
            second_binary = E.t(*(input_input), {"t-else": ""})            
            div_inner_xml.append(second_binary) 
        elif self.ttype in ["boolean"]:
            input_attrs.update({
                "t-attf-class": "s_website_form_input",
                "style": "display: block; height: 17px; width: 17px;"
            })
            div_inner_xml.append(E.input("", input_attrs))
        elif self.ttype in ["text", "html"]:
            placeholder = [E.t("", {"t-esc": field_name})]
            textararea_el = E.textarea(*(placeholder), input_attrs)
            div_inner_xml.append(textararea_el)
        elif self.ttype in ["selection"]:
            options_xml = []
            options_xml.append(E.option(u"{}".format(""), {}))
            for option in self.sel_options_ids:
                option_attrs = {
                    "value": option.key,
                    "t-att-selected": " 'selected' if {} == '{}' else null ".format(self.field_id.name, option.key)
                }
                options_xml.append(E.option(u"{}".format(option.value), option_attrs))
            div_inner_xml.append(E.select(*(options_xml), input_attrs))
        elif self.ttype in ["many2one"]:
            options_xml = []
            options_xml.append(E.option(u"{}".format(""), {}))
            options_foreach = etree.fromstring(
                u"""
                <t t-foreach="request.env['{res_model}'].sudo().search([])" t-as="line">
                    <option t-att-value="line.id" t-att-selected="'selected' if {field_name} == line.id else null">
                        <t t-esc="line.name_get()[0][1]"/>
                    </option>
                </t>
                """.format(res_model=self.res_model, field_name=self.field_id.name)
            )
            options_xml.append(options_foreach)
            div_inner_xml.append(E.select(*(options_xml), input_attrs))        
        return div_inner_xml

