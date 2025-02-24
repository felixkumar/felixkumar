from odoo import fields, models

class SyncDocumentType(models.Model):
    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
        ('export_invoice_xml', '810 - Export Invoice (SPS Commerce XML)')
    ], ondelete={'export_invoice_xml': 'cascade'})


class EdiSyncAction(models.Model):
    _inherit = 'edi.sync.action'

    def _get_documents_to_export(self):
        self.ensure_one()
        if self.doc_type_id.doc_code == 'export_invoice_xml':
            return self.env['account.move'].search([('should_export', '=', True), ('edi_status', 'in', ['pending', 'draft']), ('state', '=', 'posted')])

    def _get_export_name(self):
        self.ensure_one()
        return self.op_type
