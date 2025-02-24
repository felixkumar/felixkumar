# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


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

    def _l10n_mx_edi_get_cartaporte_pdf_values(self):
        cartaporte_values = super()._l10n_mx_edi_get_cartaporte_pdf_values()

        if self.l10n_mx_edi_is_export and self.picking_type_code in ('outgoing', 'incoming'):
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

    def _l10n_mx_edi_check_required_data(self):
        # EXTENDS 'l10n_mx_edi_stock'
        super()._l10n_mx_edi_check_required_data()

        if self.l10n_mx_edi_is_export:
            if not self.l10n_mx_edi_customs_document_type_code:
                raise UserError(_("Please define a customs regime."))
            # Code '01' corresponds to 'Pedimento'.
            if self.l10n_mx_edi_customs_document_type_code != '01' and not self.l10n_mx_edi_customs_doc_identification:
                raise UserError(_("Please define a customs document identification."))
            if self.l10n_mx_edi_importer_id and not self.l10n_mx_edi_importer_id.vat:
                raise UserError(_("Please define a VAT number for the importer."))
            if any(not move.product_id.l10n_mx_edi_material_type for move in self.move_ids):
                raise UserError(_("At least one product is missing a material type."))

    def _l10n_mx_edi_get_picking_cfdi_values(self):
        # EXTENDS 'l10n_mx_edi_stock'
        cfdi_values = super()._l10n_mx_edi_get_picking_cfdi_values()

        if self.l10n_mx_edi_is_export:
            cfdi_values['tipo_documento'] = self.l10n_mx_edi_customs_document_type_code

            # Code '01' corresponds to 'Pedimento'.
            if self.l10n_mx_edi_customs_document_type_code == '01':
                if self.picking_type_code == 'incoming':
                    cfdi_values['num_pedimento'] = self.l10n_mx_edi_pedimento_number
                    cfdi_values['rfc_impo'] = self.l10n_mx_edi_importer_id.vat
            else:
                cfdi_values['ident_doc_aduanero'] = self.l10n_mx_edi_customs_doc_identification

            if self.picking_type_code in ('outgoing', 'incoming'):
                cfdi_values['regimen_aduanero'] = self.l10n_mx_edi_customs_regime_id.code

        return cfdi_values

    def _l10n_mx_edi_get_municipio(self, partner):
        """ EXTENDS as we now have the city_id (city is only for comex)"""
        return partner.city_id.l10n_mx_edi_code or partner.city
