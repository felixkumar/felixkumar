# -*- coding: utf-8 -*-
import uuid

from werkzeug.urls import url_quote_plus

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.sql import column_exists, create_column


class Picking(models.Model):
    _inherit = 'stock.picking'

    l10n_mx_edi_is_cfdi_needed = fields.Boolean(
        compute='_compute_l10n_mx_edi_is_cfdi_needed',
        store=True,
    )
    l10n_mx_edi_idccp = fields.Char(
        string="IdCCP",
        help="Additional UUID for the Delivery Guide.",
        compute='_compute_l10n_mx_edi_idccp',
    )
    l10n_mx_edi_gross_vehicle_weight = fields.Float(
        string="Gross Vehicle Weight",
        compute="_compute_l10n_mx_edi_gross_vehicle_weight",
        store=True,
        readonly=False,
    )

    def _auto_init(self):
        if not column_exists(self.env.cr, "stock_picking", "l10n_mx_edi_gross_vehicle_weight"):
            create_column(self.env.cr, "stock_picking", "l10n_mx_edi_gross_vehicle_weight", "float8")
        if not column_exists(self.env.cr, "stock_picking", "l10n_mx_edi_is_cfdi_needed"):
            create_column(self.env.cr, "stock_picking", "l10n_mx_edi_is_cfdi_needed", "boolean")
            query = '''
                UPDATE stock_picking
                   SET l10n_mx_edi_is_cfdi_needed = True
                 WHERE id IN (
                       SELECT sp.id
                         FROM stock_picking sp
                    LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                    LEFT JOIN res_company rcomp ON sp.company_id = rcomp.id
                    LEFT JOIN res_country country ON rcomp.account_fiscal_country_id = country.id
                        WHERE country.code = 'MX' AND spt.code IN ('incoming', 'outgoing')
                )
            '''
            self.env.cr.execute(query)
        return super()._auto_init()

    @api.depends('company_id', 'picking_type_code')
    def _compute_l10n_mx_edi_is_cfdi_needed(self):
        for picking in self:
            picking.l10n_mx_edi_is_cfdi_needed = \
                picking.country_code == 'MX' \
                and picking.picking_type_code in ('incoming', 'outgoing')

    @api.depends('l10n_mx_edi_is_cfdi_needed')
    def _compute_l10n_mx_edi_idccp(self):
        for picking in self:
            if picking.l10n_mx_edi_is_cfdi_needed and not picking.l10n_mx_edi_idccp:
                # The IdCCP must be a 36 characters long RFC 4122 identifier starting with 'CCC'.
                picking.l10n_mx_edi_idccp = f'CCC{str(uuid.uuid4())[3:]}'
            else:
                picking.l10n_mx_edi_idccp = False

    @api.depends('l10n_mx_edi_vehicle_id')
    def _compute_l10n_mx_edi_gross_vehicle_weight(self):
        for picking in self:
            if picking.l10n_mx_edi_vehicle_id and not picking.l10n_mx_edi_gross_vehicle_weight:
                picking.l10n_mx_edi_gross_vehicle_weight = picking.l10n_mx_edi_vehicle_id.gross_vehicle_weight
            else:
                picking.l10n_mx_edi_gross_vehicle_weight = picking.l10n_mx_edi_gross_vehicle_weight

    def _l10n_mx_edi_check_required_data(self):
        # EXTENDS 'l10n_mx_edi_stock'
        super()._l10n_mx_edi_check_required_data()

        for picking in self:
            if picking.l10n_mx_edi_vehicle_id and not picking.l10n_mx_edi_gross_vehicle_weight:
                raise UserError(_("Please define a gross vehicle weight."))

    def _l10n_mx_edi_get_picking_cfdi_values(self):
        # EXTENDS 'l10n_mx_edi_stock'
        cfdi_values = super()._l10n_mx_edi_get_picking_cfdi_values()
        cfdi_values['idccp'] = self.l10n_mx_edi_idccp

        if self.l10n_mx_edi_vehicle_id:
            cfdi_values['peso_bruto_vehicular'] = self.l10n_mx_edi_gross_vehicle_weight

        return cfdi_values

    def _l10n_mx_edi_get_cartaporte_pdf_values(self):
        self.ensure_one()

        cfdi_values = self._l10n_mx_edi_get_picking_cfdi_values()
        warehouse_partner = self.picking_type_id.warehouse_id.partner_id
        external_trade = self.partner_id.country_code != 'MX'

        figure_types_dict = dict(self.env['l10n_mx_edi.figure']._fields['type'].selection)
        vehicle_configs_dict = dict(self.env['l10n_mx_edi.vehicle']._fields['vehicle_config'].selection)
        transport_types_dict = dict(self.env['stock.picking']._fields['l10n_mx_edi_transport_type'].selection)

        origin_partner = self.partner_id if self.picking_type_code == 'incoming' else warehouse_partner
        destination_partner = self.partner_id if self.picking_type_code == 'outgoing' else warehouse_partner

        # Generate QR code of the URL to access the service regarding the current guide document (legal requirement)
        barcode_value = url_quote_plus(f"https://verificacfdi.facturaelectronica.sat.gob.mx/verificaccp/default.aspx?"
                                       f"IdCCP={cfdi_values['idccp']}&"
                                       f"FechaOrig={cfdi_values['cfdi_date']}&"
                                       f"FechaTimb={cfdi_values['scheduled_date']}")
        barcode_src = f'/report/barcode/?barcode_type=QR&value={barcode_value}&width=180&height=180'

        return {
            'idccp': cfdi_values['idccp'] or "-",
            'transp_internac': "Sí" if external_trade else "No",
            'pais_origen_destino': f"{self.partner_id.country_id.l10n_mx_edi_code} - {self.partner_id.country_id.name}" if external_trade else "-",
            'via_entrada_salida': f"{self.l10n_mx_edi_transport_type} - {transport_types_dict.get(self.l10n_mx_edi_transport_type, '')}" if external_trade else "-",
            'total_dist_recorrida': self.l10n_mx_edi_distance or "-",
            'peso_bruto_total': cfdi_values['format_float'](sum(self.move_ids.mapped('weight')), 3),
            'unidad_peso': cfdi_values['weight_uom'].unspsc_code_id.code or "-",
            'num_total_mercancias': len(self.move_ids),
            'origen_domicilio': {
                'calle': origin_partner.street or "-",
                'codigo_postal': origin_partner.zip or "-",
                'municipio': origin_partner.city or "-",
                'estado': f"{origin_partner.state_id.code} - {origin_partner.state_id.name}" or "-",
                'pais': f"{origin_partner.country_id.l10n_mx_edi_code} - {origin_partner.country_id.name}" or "-",
            },
            'destino_domicilio': {
                'calle': destination_partner.street or "-",
                'codigo_postal': destination_partner.zip or "-",
                'municipio': destination_partner.city or "-",
                'estado': f"{destination_partner.state_id.code} - {destination_partner.state_id.name}" or "-",
                'pais': f"{destination_partner.country_id.l10n_mx_edi_code} - {destination_partner.country_id.name}" or "-",
            },
            'origen_ubicacion': {
                'id_ubicacion': "OR" + str(self.location_id.id).rjust(6, "0"),
                'rfc_remitente_destinatario': "XEXX010101000"
                    if origin_partner.country_id.l10n_mx_edi_code != 'MEX'
                    else origin_partner.commercial_partner_id.vat or "-",
                'num_reg_id_trib': cfdi_values['supplier'].vat
                    if origin_partner.country_id.l10n_mx_edi_code != 'MEX'
                    else "-",
                'residencia_fiscal': f"{origin_partner.country_id.l10n_mx_edi_code} - {origin_partner.country_id.name}"
                    if origin_partner.country_id.l10n_mx_edi_code != 'MEX'
                    else "-",
                'fecha_hora_salida_llegada': cfdi_values['cfdi_date'] or "-",
            },
            'destino_ubicacion': {
                'id_ubicacion': "DE" + str(self.location_dest_id.id).rjust(6, "0"),
                'rfc_remitente_destinatario': "XEXX010101000"
                    if destination_partner.country_id.l10n_mx_edi_code != 'MEX'
                    else destination_partner.commercial_partner_id.vat or "-",
                'num_reg_id_trib': destination_partner.commercial_partner_id.vat or "-"
                    if destination_partner.country_id.l10n_mx_edi_code != 'MEX'
                    else "-",
                'residencia_fiscal': f"{destination_partner.country_id.l10n_mx_edi_code} - {destination_partner.country_id.name}"
                    if destination_partner.country_id.l10n_mx_edi_code != 'MEX'
                    else "-",
                'fecha_hora_salida_llegada': cfdi_values['scheduled_date'] or "-",
                'distancia_recorrida': self.l10n_mx_edi_distance or "-",
            },
            'transport_perm_sct': self.l10n_mx_edi_vehicle_id.transport_perm_sct or "-",
            'num_permiso_sct': self.l10n_mx_edi_vehicle_id.name or "-",
            'config_vehicular': f"{self.l10n_mx_edi_vehicle_id.vehicle_config} - {vehicle_configs_dict.get(self.l10n_mx_edi_vehicle_id.vehicle_config, '')}",
            'peso_bruto_vehicular': self.l10n_mx_edi_gross_vehicle_weight if self.l10n_mx_edi_vehicle_id else "-",
            'placa_vm': self.l10n_mx_edi_vehicle_id.vehicle_licence or "-",
            'anio_modelo_vm': self.l10n_mx_edi_vehicle_id.vehicle_model or "-",
            'asegura_resp_civil': self.l10n_mx_edi_vehicle_id.transport_insurer or "-",
            'poliza_resp_civil': self.l10n_mx_edi_vehicle_id.transport_insurance_policy or "-",
            'figures': [
                {
                    'tipo_figura': f"{figure.type} - {figure_types_dict.get(figure.type, '')}",
                    'num_licencia': (figure.type == '01' and figure.operator_id.l10n_mx_edi_operator_licence) or "-",
                    'num_reg_id_trib_figura': figure.operator_id.vat or "-"
                        if figure.operator_id.country_id.l10n_mx_edi_code != 'MEX'
                        else "-",
                    'residencia_fiscal_figura': f"{figure.operator_id.country_id.l10n_mx_edi_code} - {figure.operator_id.country_id.name}" or "-"
                        if figure.operator_id.country_id.l10n_mx_edi_code != 'MEX'
                        else "-",
                }
                for figure in self.l10n_mx_edi_vehicle_id.figure_ids.sorted('type')
            ],
            'barcode_src': barcode_src,
        }

    def _l10n_mx_edi_dg_render(self, values):
        # OVERRIDES 'l10n_mx_edi_stock'
        cfdi = self.env['ir.qweb']._render('l10n_mx_edi_stock_30.cfdi_cartaporte_30', values)
        carta_porte_20 = str(cfdi)
        # Since we are inheriting version 2.0 of the Carta Porte template,
        # we need to update both the namespace prefix and its URI to version 3.0.
        carta_porte_30 = carta_porte_20 \
            .replace('cartaporte20', 'cartaporte30') \
            .replace('CartaPorte20', 'CartaPorte30')
        return bytes(carta_porte_30, 'utf-8')

    def _l10n_mx_edi_get_municipio(self, partner):
        """ To be overridden as we do not have the city code without extended"""
        return None

    def l10n_mx_edi_action_print_cartaporte(self):
        return self.env.ref('l10n_mx_edi_stock_30.action_report_cartaporte').report_action(self)
