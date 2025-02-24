# -*- coding: utf-8 -*-
import uuid

from werkzeug.urls import url_quote_plus

from odoo import _, api, fields, models
from odoo.tools.sql import column_exists, create_column


class Picking(models.Model):
    _inherit = 'stock.picking'

    l10n_mx_edi_is_delivery_guide_needed = fields.Boolean(compute='_compute_l10n_mx_edi_is_delivery_guide_needed')
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
    def _compute_l10n_mx_edi_is_delivery_guide_needed(self):
        for picking in self:
            picking.l10n_mx_edi_is_delivery_guide_needed = (
                picking.country_code == 'MX'
                and picking.picking_type_code in ('incoming', 'outgoing')
            )

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

    def _compute_l10n_mx_edi_is_cfdi_needed(self):
        # OVERRIDES 'l10n_mx_edi_stock'
        for picking in self:
            picking.l10n_mx_edi_is_cfdi_needed = (
                picking.l10n_mx_edi_is_delivery_guide_needed
                and picking.state == 'done'
            )

    def _l10n_mx_edi_cfdi_check_picking_config(self):
        # EXTENDS 'l10n_mx_edi_stock'
        errors = super()._l10n_mx_edi_cfdi_check_picking_config()

        if self.l10n_mx_edi_vehicle_id and not self.l10n_mx_edi_gross_vehicle_weight:
            errors.append(_("Please define a gross vehicle weight."))

        return errors

    @api.model
    def _l10n_mx_edi_add_domicilio_cfdi_values(self, cfdi_values, partner):
        cfdi_values['domicilio'] = {
            'calle': partner.street,
            'codigo_postal': partner.zip,
            'estado': partner.state_id.code,
            'pais': partner.country_id.l10n_mx_edi_code,
            'municipio': None,
        }

    def _l10n_mx_edi_add_picking_cfdi_values(self, cfdi_values):
        # EXTENDS 'l10n_mx_edi_stock'
        super()._l10n_mx_edi_add_picking_cfdi_values(cfdi_values)
        cfdi_values['idccp'] = self.l10n_mx_edi_idccp

        if self.l10n_mx_edi_vehicle_id:
            cfdi_values['peso_bruto_vehicular'] = self.l10n_mx_edi_gross_vehicle_weight
        else:
            cfdi_values['peso_bruto_vehicular'] = None

        warehouse_partner = self.picking_type_id.warehouse_id.partner_id
        receptor = cfdi_values['receptor']
        emisor = cfdi_values['emisor']

        cfdi_values['origen'] = {
            'id_ubicacion': f"OR{str(self.location_id.id).rjust(6, '0')}",
            'fecha_hora_salida_llegada': cfdi_values['cfdi_date'],
            'num_reg_id_trib': None,
            'residencia_fiscal': None,
        }
        cfdi_values['destino'] = {
            'id_ubicacion': f"DE{str(self.location_dest_id.id).rjust(6, '0')}",
            'fecha_hora_salida_llegada': cfdi_values['scheduled_date'],
            'num_reg_id_trib': None,
            'residencia_fiscal': None,
            'distancia_recorrida': self.l10n_mx_edi_distance,
        }

        if self.picking_type_code == 'outgoing':
            cfdi_values['destino']['rfc_remitente_destinatario'] = receptor['rfc']
            if self.l10n_mx_edi_external_trade:
                cfdi_values['destino']['num_reg_id_trib'] = receptor['customer'].vat
                cfdi_values['destino']['residencia_fiscal'] = receptor['customer'].country_id.l10n_mx_edi_code
            if warehouse_partner.country_id.l10n_mx_edi_code != 'MEX':
                cfdi_values['origen']['rfc_remitente_destinatario'] = 'XEXX010101000'
                cfdi_values['origen']['num_reg_id_trib'] = emisor['supplier'].vat
                cfdi_values['origen']['residencia_fiscal'] = warehouse_partner.country_id.l10n_mx_edi_code
            else:
                cfdi_values['origen']['rfc_remitente_destinatario'] = emisor['rfc']
            self._l10n_mx_edi_add_domicilio_cfdi_values(cfdi_values['origen'], warehouse_partner)
            self._l10n_mx_edi_add_domicilio_cfdi_values(cfdi_values['destino'], self.partner_id)
        else:
            cfdi_values['origen']['rfc_remitente_destinatario'] = receptor['rfc']
            if self.l10n_mx_edi_external_trade:
                cfdi_values['origen']['num_reg_id_trib'] = receptor['customer'].vat
                cfdi_values['origen']['residencia_fiscal'] = receptor['customer'].country_id.l10n_mx_edi_code
            if warehouse_partner.country_id.l10n_mx_edi_code != 'MEX':
                cfdi_values['destino']['rfc_remitente_destinatario'] = 'XEXX010101000'
                cfdi_values['destino']['num_reg_id_trib'] = emisor['supplier'].vat
                cfdi_values['destino']['residencia_fiscal'] = warehouse_partner.country_id.l10n_mx_edi_code
            else:
                cfdi_values['destino']['rfc_remitente_destinatario'] = emisor['rfc']
            self._l10n_mx_edi_add_domicilio_cfdi_values(cfdi_values['origen'], self.partner_id)
            self._l10n_mx_edi_add_domicilio_cfdi_values(cfdi_values['destino'], warehouse_partner)

    def _l10n_mx_edi_get_cartaporte_pdf_values(self):
        self.ensure_one()

        cfdi_values = self.env['l10n_mx_edi.document']._get_company_cfdi_values(self.company_id)
        self.env['l10n_mx_edi.document']._add_certificate_cfdi_values(cfdi_values)
        self._l10n_mx_edi_add_picking_cfdi_values(cfdi_values)

        warehouse_partner = self.picking_type_id.warehouse_id.partner_id

        figure_types_dict = dict(self.env['l10n_mx_edi.figure']._fields['type'].selection)
        vehicle_configs_dict = dict(self.env['l10n_mx_edi.vehicle']._fields['vehicle_config'].selection)
        transport_types_dict = dict(self.env['stock.picking']._fields['l10n_mx_edi_transport_type'].selection)

        ubicacion_fields = (
            'id_ubicacion',
            'rfc_remitente_destinatario',
            'num_reg_id_trib',
            'residencia_fiscal',
            'fecha_hora_salida_llegada',
        )

        origin_partner = self.partner_id if self.picking_type_code == 'incoming' else warehouse_partner
        destination_partner = self.partner_id if self.picking_type_code == 'outgoing' else warehouse_partner

        # Add legible data to the origin and destination addresses
        if cfdi_values['origen']['domicilio']['estado']:
            cfdi_values['origen']['domicilio']['estado'] += f" - {origin_partner.state_id.name}"
        if cfdi_values['origen']['domicilio']['pais']:
            cfdi_values['origen']['domicilio']['pais'] += f" - {origin_partner.country_id.name}"
        if cfdi_values['destino']['domicilio']['estado']:
            cfdi_values['destino']['domicilio']['estado'] += f" - {destination_partner.state_id.name}"
        if cfdi_values['destino']['domicilio']['pais']:
            cfdi_values['destino']['domicilio']['pais'] += f" - {destination_partner.country_id.name}"

        # Generate QR code of the URL to access the service regarding the current guide document (legal requirement)
        barcode_value = url_quote_plus(f"https://verificacfdi.facturaelectronica.sat.gob.mx/verificaccp/default.aspx?"
                                       f"IdCCP={cfdi_values['idccp']}&"
                                       f"FechaOrig={cfdi_values['cfdi_date']}&"
                                       f"FechaTimb={cfdi_values['scheduled_date']}")
        barcode_src = f'/report/barcode/?barcode_type=QR&value={barcode_value}&width=180&height=180'

        return {
            'idccp': cfdi_values['idccp'] or "-",
            'transp_internac': "Sí" if self.l10n_mx_edi_external_trade else "No",
            'pais_origen_destino': f"{self.partner_id.country_id.l10n_mx_edi_code} - {self.partner_id.country_id.name}" if self.l10n_mx_edi_external_trade else "-",
            'via_entrada_salida': f"{self.l10n_mx_edi_transport_type} - {transport_types_dict.get(self.l10n_mx_edi_transport_type, '')}" if self.l10n_mx_edi_external_trade else "-",
            'total_dist_recorrida': self.l10n_mx_edi_distance or "-",
            'peso_bruto_total': cfdi_values['format_float'](sum(self.move_ids.mapped('weight')), 3),
            'unidad_peso': cfdi_values['weight_uom'].unspsc_code_id.code or "-",
            'num_total_mercancias': len(self.move_ids),
            'origen_domicilio': {
                field: value or "-" for field, value in cfdi_values['origen']['domicilio'].items()
            },
            'destino_domicilio': {
                field: value or "-" for field, value in cfdi_values['destino']['domicilio'].items()
            },
            'origen_ubicacion': {
                field: cfdi_values['origen'][field] or "-" for field in ubicacion_fields
            },
            'destino_ubicacion': {
                field: cfdi_values['destino'][field] or "-" for field in (*ubicacion_fields, 'distancia_recorrida')
            },
            'transport_perm_sct': self.l10n_mx_edi_vehicle_id.transport_perm_sct or "-",
            'num_permiso_sct': self.l10n_mx_edi_vehicle_id.name or "-",
            'config_vehicular': f"{self.l10n_mx_edi_vehicle_id.vehicle_config} - {vehicle_configs_dict.get(self.l10n_mx_edi_vehicle_id.vehicle_config, '')}",
            'peso_bruto_vehicular': cfdi_values['peso_bruto_vehicular'] or "-",
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

    @api.model
    def _l10n_mx_edi_prepare_picking_cfdi_template(self):
        # OVERRIDES 'l10n_mx_edi_stock'
        return 'l10n_mx_edi_stock_30.cfdi_cartaporte_30'

    def l10n_mx_edi_action_print_cartaporte(self):
        return self.env.ref('l10n_mx_edi_stock_30.action_report_cartaporte').report_action(self)
