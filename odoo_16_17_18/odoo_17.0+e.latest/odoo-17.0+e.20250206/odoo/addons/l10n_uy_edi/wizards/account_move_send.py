from odoo import models, fields, api, _


class AccountMoveSend(models.TransientModel):
    _inherit = "account.move.send"

    l10n_uy_edi_show_checkbox_cfe = fields.Boolean(compute="_compute_send_mail_extra_fields")
    l10n_uy_edi_checkbox_cfe = fields.Boolean(
        compute="_compute_l10n_uy_edi_checkbox_cfe",
        string="Create CFE",
        store=True,
        readonly=False,
        help="Uruguay: used to determine whether to submit this e-invoice.",
    )
    l10n_uy_edi_warning = fields.Text(
        "Uruguay: Warning",
        compute="_compute_l10n_uy_edi_warning",
        readonly=True,
        help="Uruguay: used to display warnings in the wizard before sending.",
    )

    # Compute methods

    @api.depends("l10n_uy_edi_show_checkbox_cfe", "move_ids")
    def _compute_l10n_uy_edi_checkbox_cfe(self):
        for wizard in self:
            # Enable e-invoicing by default if possible for this invoice.
            wizard.l10n_uy_edi_checkbox_cfe = wizard.l10n_uy_edi_show_checkbox_cfe

    @api.depends("l10n_uy_edi_checkbox_cfe", "move_ids")
    def _compute_l10n_uy_edi_warning(self):
        self.l10n_uy_edi_warning = False
        for wizard in self.filtered("l10n_uy_edi_checkbox_cfe"):
            if non_eligible := self.move_ids.filtered(lambda move: not move.l10n_uy_edi_is_needed):
                wizard.l10n_uy_edi_warning = _(
                    "Uruguayan e-invoicing was enabled but the following invoices cannot be e-invoiced:\n%s\n"
                    "If this is not intended, please check if an UCFE Uruware is properly set or if the invoice"
                    " isn't already e-invoiced.\n", "".join(f"- {move.display_name}" for move in non_eligible))

    def _compute_send_mail_extra_fields(self):
        # EXTENDS "account"
        super()._compute_send_mail_extra_fields()
        for wizard in self:
            wizard.l10n_uy_edi_show_checkbox_cfe = any(move.l10n_uy_edi_is_needed for move in wizard.move_ids)

    @api.depends("enable_download")
    def _compute_checkbox_download(self):
        """ We dont want to download ZIP with XML and PDF everytime we create a CFE """
        super()._compute_checkbox_download()
        self.filtered(lambda x: x.l10n_uy_edi_checkbox_cfe).checkbox_download = False

    # Other methods

    @api.model
    def _hook_invoice_document_before_pdf_report_render(self, invoice, invoice_data):
        # EXTENDS "account"
        super()._hook_invoice_document_before_pdf_report_render(invoice, invoice_data)
        if invoice_data.get("l10n_uy_edi_checkbox_cfe") and invoice.l10n_uy_edi_is_needed:
            if errors := invoice._l10n_uy_edi_check_move():
                invoice_data["error"] = {
                    "error_title": _("Errors occurred while creating the EDI document (CFE):"),
                    "errors": errors,
                }

    def _call_web_service_before_invoice_pdf_render(self, invoices_data):
        # EXTENDS "account"
        super()._call_web_service_before_invoice_pdf_render(invoices_data)

        for invoice, invoice_data in invoices_data.items():
            # Not all invoices may need EDI.
            if not invoice_data.get("l10n_uy_edi_checkbox_cfe") or not invoice.l10n_uy_edi_is_needed:
                continue

            invoice._l10n_uy_edi_send()
            if invoice.l10n_uy_edi_error:
                invoice_data["error"] = {
                    "error_title": _("Errors when submitting the e-invoice:"),
                    "errors": [invoice.l10n_uy_edi_error],
                }

            if self._can_commit():
                self._cr.commit()

    def _get_invoice_extra_attachments(self, move):
        # EXTENDS "account"
        return super()._get_invoice_extra_attachments(move) + move.l10n_uy_edi_xml_attachment_id

    def _get_placeholder_mail_attachments_data(self, move):
        # EXTENDS "account"
        res = super()._get_placeholder_mail_attachments_data(move)

        if self.l10n_uy_edi_show_checkbox_cfe and self.l10n_uy_edi_checkbox_cfe:
            attachment_name = move.l10n_uy_edi_document_id._get_xml_attachment_name()
            res.append({
                "id": f"placeholder_{attachment_name}",
                "name": attachment_name,
                "mimetype": "application/xml",
                "placeholder": True,
            })
        return res

    def _get_wizard_values(self):
        # EXTENDS "account"
        res = super()._get_wizard_values()
        res["l10n_uy_edi_checkbox_cfe"] = self.l10n_uy_edi_checkbox_cfe
        return res

    def _hook_if_success(self, moves_data, from_cron=False, allow_fallback_pdf=False):
        # EXTENDS "account"
        for move in moves_data:
            if move.l10n_uy_edi_cfe_state in ("received", "accepted"):
                mail_template = moves_data[move]["mail_template_id"]
                mail_lang = moves_data[move]["mail_lang"]
                moves_data[move].update({
                    "mail_body": self._get_default_mail_body(move, mail_template, mail_lang),
                    "mail_subject": self._get_default_mail_subject(move, mail_template, mail_lang),
                })
        return super()._hook_if_success(moves_data, from_cron=from_cron, allow_fallback_pdf=allow_fallback_pdf)
