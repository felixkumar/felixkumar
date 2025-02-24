import re

from lxml import etree

from odoo import fields, models


class Picking(models.Model):
    _inherit = 'stock.picking'

    l10n_mx_edi_customs_regime_ids = fields.Many2many(
        string="Customs Regimes",
        help="Regimes associated to the good's transfer (import or export).",
        comodel_name='l10n_mx_edi.customs.regime',
        ondelete='restrict',
    )

    def _l10n_mx_edi_get_cartaporte_pdf_values(self):
        # EXTENDS 'l10n_mx_edi_stock_extended_30'
        cartaporte_values = super()._l10n_mx_edi_get_cartaporte_pdf_values()

        if self.l10n_mx_edi_is_export and self.picking_type_code in ('outgoing', 'incoming'):
            # 'regimen_aduanero' has been replaced by a new 'regimenes_aduanero' Many2many relationship.
            # We keep the key here (with a None value) for backward compatibility.
            cartaporte_values['regimen_aduanero'] = None
            cartaporte_values['regimenes_aduanero'] = ", ".join(self.l10n_mx_edi_customs_regime_ids.mapped('code'))

        return cartaporte_values

    def _l10n_mx_edi_get_picking_cfdi_values(self):
        # EXTENDS 'l10n_mx_edi_stock'
        cfdi_values = super()._l10n_mx_edi_get_picking_cfdi_values()

        if self.l10n_mx_edi_is_export and self.picking_type_code in ('outgoing', 'incoming'):
            # 'regimen_aduanero' has been replaced by a new 'regimenes_aduanero' Many2many relationship.
            # We keep the key here (with a None value) for backward compatibility.
            cfdi_values['regimen_aduanero'] = None
            cfdi_values['regimenes_aduanero'] = self.l10n_mx_edi_customs_regime_ids.mapped('code')

        return cfdi_values

    def _l10n_mx_edi_dg_render(self, values):
        # OVERRIDES 'l10n_mx_edi_stock'
        cfdi = self.env['ir.qweb']._render('l10n_mx_edi_stock_extended_31.cfdi_cartaporte_comex_31', values)

        # The CartaPorte node will only be rendered in the XML if 'Transport Type' is set to 'Federal Transport' ('01').
        if self.l10n_mx_edi_transport_type != '01':
            return cfdi

        # Due to the multiple inherits and position="replace" used in the XML templates,
        # we need to manually rearrange the order of the CartaPorte node's children using lxml etree.
        carta_porte_20_etree = etree.fromstring(str(cfdi))
        carta_porte_element = carta_porte_20_etree.find('.//{*}CartaPorte')
        regimenes_aduanero_element = carta_porte_element.find('.//{*}RegimenesAduaneros')
        if regimenes_aduanero_element is not None:
            carta_porte_element.remove(regimenes_aduanero_element)
            carta_porte_element.insert(0, regimenes_aduanero_element)
        carta_porte_20 = etree.tostring(carta_porte_20_etree).decode()

        # Since we are inheriting versions 2.0 and 3.0 of the Carta Porte template,
        # we need to update both the namespace prefix and its URI to version 3.1.
        carta_porte_31 = re.sub(r'([cC]arta[pP]orte)[23]0', r'\g<1>31', carta_porte_20)

        return bytes(carta_porte_31, 'utf-8')
