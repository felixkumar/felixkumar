from odoo import api, fields, models

class SyncDocumentType(models.Model):
    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
        ('export_sale_acknowledgement_xml', '855 - Export Purchase Order Acknowledgement (SPS Commerce XML)')
    ], ondelete={'export_sale_acknowledgement_xml': 'cascade'})


class EdiSyncAction(models.Model):
    _inherit = 'edi.sync.action'

    def _get_documents_to_export(self):
        self.ensure_one()
        if self.doc_type_id.doc_code == 'export_sale_acknowledgement_xml':
            return self.env['sale.order'].sudo().search([('partner_id.send_edi_order_ack', '=', True),
                                                         ('edi_status', 'in', ['draft', 'pending']),
                                                         ('state', '=', 'sale')])
        else:
            return super()._get_documents_to_export()
