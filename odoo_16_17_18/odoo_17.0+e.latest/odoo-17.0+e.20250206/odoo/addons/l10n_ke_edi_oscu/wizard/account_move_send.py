# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountMoveSend(models.TransientModel):
    _inherit = 'account.move.send'

    l10n_ke_show_checkbox_oscu = fields.Boolean(compute="_compute_l10n_ke_show_checkbox_oscu")
    l10n_ke_checkbox_oscu = fields.Boolean(
        string='Send to eTIMS',
        default='_get_default_l10n_ke_edi_oscu_enable',
        help='Send the invoice to the KRA',
    )

    @api.depends('move_ids')
    def _compute_l10n_ke_show_checkbox_oscu(self):
        for wizard in self:
            wizard.l10n_ke_show_checkbox_oscu = any(self._get_default_l10n_ke_edi_oscu_enable(move) for move in wizard.move_ids)

    def _get_default_l10n_ke_edi_oscu_enable(self, move):
        return move.company_id.l10n_ke_oscu_is_active and not move.l10n_ke_oscu_receipt_number

    def _get_wizard_values(self):
        # EXTENDS 'account'
        values = super()._get_wizard_values()
        values['l10n_ke_oscu'] = self.l10n_ke_checkbox_oscu
        return values

    # -------------------------------------------------------------------------
    # BUSINESS ACTIONS
    # -------------------------------------------------------------------------

    @api.model
    def _call_web_service_before_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_before_invoice_pdf_render(invoices_data)

        for invoice, invoice_data in invoices_data.items():
            if invoice_data.get('l10n_ke_oscu') and self._get_default_l10n_ke_edi_oscu_enable(invoice):
                validation_messages = (invoice.l10n_ke_validation_message or {}).values()
                if (blocking := [msg for msg in validation_messages if msg.get('blocking')]):
                    invoice_data['error'] = {
                        'error_title': _("Can't send to eTIMS"),
                        'errors': [msg['message'] for msg in blocking],
                    }
                    continue
                _content, error = invoice._l10n_ke_oscu_send_customer_invoice()

                if error:
                    invoice_data['error'] = {
                        'error_title': _("Error when sending to the KRA:"),
                        'errors': [error['message']],
                    }

                if self._can_commit():
                    self._cr.commit()
