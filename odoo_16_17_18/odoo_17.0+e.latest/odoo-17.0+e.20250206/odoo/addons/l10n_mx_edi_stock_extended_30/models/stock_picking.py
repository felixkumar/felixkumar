# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class Picking(models.Model):
    _inherit = 'stock.picking'

    # DEPRECATED -> This field has been replaced by a Many2many in 'l10n_mx_edi_stock_extended_31'
    l10n_mx_edi_customs_regime_id = fields.Many2one(
        string="Customs Regime",
        help="Regime associated to the good's transfer (import or export).",
        comodel_name='l10n_mx_edi.customs.regime',
        ondelete="restrict",
    )
    l10n_mx_edi_customs_document_type_id = fields.Many2one(
        string="Customs Document Type",
        help="Type of customs document associated with the transport of the goods.",
        comodel_name='l10n_mx_edi.customs.document.type',
        ondelete="restrict",
    )
    l10n_mx_edi_customs_document_type_code = fields.Char(related='l10n_mx_edi_customs_document_type_id.code')
    l10n_mx_edi_pedimento_number = fields.Char(
        string="Pedimento Number",
        help="Pedimento number associated with the import of the goods.",
    )
    l10n_mx_edi_customs_doc_identification = fields.Char(
        string="Customs Document Identification",
        help="Folio of the customs document associated with the import of the goods.",
    )
    l10n_mx_edi_importer_id = fields.Many2one(
        string="Importer",
        help="Importer registered in the customs documentation.",
        comodel_name='res.partner',
        ondelete="restrict",
    )

    def _l10n_mx_edi_cfdi_check_picking_config(self):
        # EXTENDS 'l10n_mx_edi_stock'
        errors = super()._l10n_mx_edi_cfdi_check_picking_config()

        if self.l10n_mx_edi_external_trade:

            pedimento_code = self.env.ref('l10n_mx_edi_stock_extended_30.l10n_mx_edi_customs_document_type_01').code

            if not self.l10n_mx_edi_customs_document_type_code:
                errors.append(_("Please define a customs regime."))
            if self.l10n_mx_edi_customs_document_type_code != pedimento_code and not self.l10n_mx_edi_customs_doc_identification:
                errors.append(_("Please define a customs document identification."))
            if self.l10n_mx_edi_importer_id and not self.l10n_mx_edi_importer_id.vat:
                errors.append(_("Please define a VAT number for the importer '%s'.", self.l10n_mx_edi_importer_id.name))
            if any(not move.product_id.l10n_mx_edi_material_type for move in self.move_ids):
                errors.append(_("At least one product is missing a material type."))

        return errors

    @api.model
    def _l10n_mx_edi_add_domicilio_cfdi_values(self, cfdi_values, partner):
        # EXTENDS 'l10n_mx_edi_stock'
        super()._l10n_mx_edi_add_domicilio_cfdi_values(cfdi_values, partner)
        cfdi_values['domicilio']['municipio'] = partner.city_id.l10n_mx_edi_code or partner.city

    def _l10n_mx_edi_add_picking_cfdi_values(self, cfdi_values):
        # EXTENDS 'l10n_mx_edi_stock'
        super()._l10n_mx_edi_add_picking_cfdi_values(cfdi_values)

        if self.l10n_mx_edi_external_trade:
            cfdi_values['tipo_documento'] = self.l10n_mx_edi_customs_document_type_code

            # Code '01' corresponds to 'Pedimento'.
            if self.l10n_mx_edi_customs_document_type_code == '01':
                if self.picking_type_code == 'incoming':
                    cfdi_values['num_pedimento'] = self.l10n_mx_edi_pedimento_number
                    cfdi_values['rfc_impo'] = self.l10n_mx_edi_importer_id.vat
            else:
                cfdi_values['ident_doc_aduanero'] = self.l10n_mx_edi_customs_doc_identification

            if self.picking_type_code in ('outgoing', 'incoming'):
                cfdi_values['entrada_salida_merc'] = 'Salida' if self.picking_type_code == 'outgoing' else 'Entrada'
                cfdi_values['regimen_aduanero'] = self.l10n_mx_edi_customs_regime_id.code

    def _l10n_mx_edi_get_cartaporte_pdf_values(self):
        # EXTENDS 'l10n_mx_edi_stock_30'
        cartaporte_values = super()._l10n_mx_edi_get_cartaporte_pdf_values()

        warehouse_partner = self.picking_type_id.warehouse_id.partner_id
        origin_partner = self.partner_id if self.picking_type_code == 'incoming' else warehouse_partner
        destination_partner = self.partner_id if self.picking_type_code == 'outgoing' else warehouse_partner

        # Add legible data to the origin and destination addresses
        if cartaporte_values['origen_domicilio']['municipio'] != origin_partner.city:
            cartaporte_values['origen_domicilio']['municipio'] += f" - {origin_partner.city}"
        if cartaporte_values['destino_domicilio']['municipio'] != destination_partner.city:
            cartaporte_values['destino_domicilio']['municipio'] += f" - {destination_partner.city}"
        origen_res_fisc = cartaporte_values['origen_ubicacion']['residencia_fiscal']
        origen_country_name = self.env['res.country'].search([('l10n_mx_edi_code', '=', origen_res_fisc)], limit=1).name
        if origen_country_name:
            origen_res_fisc += f" - {origen_country_name}"
        destino_res_fisc = cartaporte_values['destino_ubicacion']['residencia_fiscal']
        destino_country_name = self.env['res.country'].search([('l10n_mx_edi_code', '=', destino_res_fisc)], limit=1).name
        if destino_country_name:
            destino_res_fisc += f" - {destino_country_name}"

        if self.picking_type_code in ('outgoing', 'incoming'):
            cartaporte_values['entrada_salida_merc'] = "Salida" if self.picking_type_code == 'outgoing' else "Entrada"

        contains_hazardous_materials = any(self.move_ids.product_id.mapped('l10n_mx_edi_hazardous_material_code'))
        return {
            **cartaporte_values,
            'asegura_med_ambiente': self.l10n_mx_edi_vehicle_id.environment_insurer
                if contains_hazardous_materials
                else "-",
            'poliza_med_ambiente': self.l10n_mx_edi_vehicle_id.environment_insurance_policy
                if contains_hazardous_materials
                else "-",
        }
