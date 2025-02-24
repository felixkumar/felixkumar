from odoo import http, _
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class L10nCOWebsiteSale(WebsiteSale):

    def _get_mandatory_fields_billing(self, country_id=False):
        mandatory_fields = super()._get_mandatory_fields_billing(country_id)
        company_country = request.website.sudo().company_id.account_fiscal_country_id
        if company_country.code == 'CO' and country_id == company_country.id:
            mandatory_fields += ["vat", "city_id", "state_id", "l10n_latam_identification_type_id"]
            mandatory_fields.remove("city")
        return mandatory_fields

    def _get_mandatory_fields_shipping(self, country_id=False):
        mandatory_fields = super()._get_mandatory_fields_shipping(country_id)
        company_country = request.website.sudo().company_id.account_fiscal_country_id
        if company_country.code == 'CO' and country_id == company_country.id:
            mandatory_fields += ["city_id", "state_id"]
            mandatory_fields.remove("city")
        return mandatory_fields

    def values_preprocess(self, values):
        new_values = super().values_preprocess(values)
        website = request.env['website'].get_current_website()
        if website.company_id.account_fiscal_country_id.code == 'CO':
            # This is needed so that the field is correctly read as list from the request
            if new_values.get('l10n_co_edi_obligation_type_ids'):
                new_values['l10n_co_edi_obligation_type_ids'] = request.httprequest.form.getlist('l10n_co_edi_obligation_type_ids')
            # Set default values for fiscal regimen and obligation types when identification type is not NIT
            id_type_id = new_values.get("l10n_latam_identification_type_id")
            id_type = request.env['l10n_latam.identification.type'].browse(id_type_id)
            if id_type and id_type.name != 'NIT':
                default_obligations = ['R-99-PN']
                default_obligations_ids = request.env['l10n_co_edi.type_code'].sudo().search([('name', 'in', default_obligations)])
                new_values.update({
                    'l10n_co_edi_fiscal_regimen': '49',  # No Aplica
                    'l10n_co_edi_obligation_type_ids': default_obligations_ids,
                })
        return new_values

    def _get_vat_validation_fields(self, data):
        res = super()._get_vat_validation_fields(data)
        latam_id_type_data = data.get("l10n_latam_identification_type_id")
        if request.website.sudo().company_id.account_fiscal_country_id.code == "CO":
            res.update({
                'l10n_latam_identification_type_id': int(latam_id_type_data) if latam_id_type_data else False,
                'name': data.get('name', False),
            })
        return res

    def checkout_form_validate(self, mode, all_form_values, data):
        error, error_message = super().checkout_form_validate(mode, all_form_values, data)

        if request.website.sudo().company_id.account_fiscal_country_id.code == "CO" and mode[1] == 'billing':
            if error and any(field in error for field in ['l10n_latam_identification_type_id', 'l10n_co_edi_obligation_type_ids', 'l10n_co_edi_fiscal_regimen']):
                return error, error_message
            id_type_id = data.get("l10n_latam_identification_type_id")
            id_type = request.env['l10n_latam.identification.type'].browse(id_type_id)
            if id_type and id_type.name == 'NIT':
                if not data.get('l10n_co_edi_obligation_type_ids'):
                    error['l10n_co_edi_obligation_type_ids'] = 'missing'
                    error_message.append(_("Obligation is required for the NIT identification type."))
                if not data.get('l10n_co_edi_fiscal_regimen'):
                    error['l10n_co_edi_fiscal_regimen'] = 'missing'
                    error_message.append(_("Fiscal Regimen is required for NIT identification type."))
                if not data.get('company_name'):
                    error['company_name'] = 'missing'
                    error_message.append(_("Company name is required for NIT identification type."))
        return error, error_message

    def _get_country_related_render_values(self, kw, render_values):
        res = super()._get_country_related_render_values(kw, render_values)

        if request.website.sudo().company_id.account_fiscal_country_id.code == "CO":
            values = render_values["checkout"]
            state = "state_id" in values and request.env["res.country.state"].browse(int(values["state_id"]))
            city = "city_id" in values and request.env["res.city"].browse(int(values["city_id"]))
            fiscal_regimen = "l10n_co_edi_fiscal_regimen" in values and values["l10n_co_edi_fiscal_regimen"]
            selected_obligation_types_ids = request.httprequest.form.getlist('l10n_co_edi_obligation_type_ids', int) or []
            to_include = {
                "identification": kw.get("l10n_latam_identification_type_id"),
                "identification_types": request.env["l10n_latam.identification.type"].sudo().search([("country_id.code", "=", "CO")]),
                "selected_obligation_types_ids": selected_obligation_types_ids,
                "obligation_types": request.env["l10n_co_edi.type_code"].sudo().search([]),
                "fiscal_regimen": fiscal_regimen,
                "fiscal_regimen_selection": request.env["res.partner"]._fields["l10n_co_edi_fiscal_regimen"].selection,
            }
            if state:
                to_include.update({
                    "state": state,
                    "state_cities": request.env["res.city"].sudo().search([("state_id", "=", state.id)]),
                })
            if city:
                to_include["city"] = city
            res.update(to_include)
        return res

    @http.route(
        ['/shop/l10n_co_state_infos/<model("res.country.state"):state>'],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def l10n_co_state_infos(self, state, **kw):
        cities = request.env["res.city"].sudo().search([("state_id", "=", state.id)])
        return {'cities': [(c.id, c.name, c.l10n_co_edi_code) for c in cities]}
