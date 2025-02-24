from odoo import api, fields, models


class SyncDocumentType(models.Model):
    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
        ('export_shipment_xml', '856 - Delivery (SPS Commerce XML)')
    ], ondelete={'export_shipment_xml': 'cascade'})


class EdiSyncAction(models.Model):
    _inherit = 'edi.sync.action'

    def _get_documents_to_export(self):
        self.ensure_one()
        if self.doc_type_id.doc_code == 'export_shipment_xml':
            return self.env['stock.picking'].sudo().search([('partner_id.outbound_edi_asn', '=', True),
                                                            ('picking_type_code', '=', 'outgoing'),
                                                            ('state', '=', 'done'),
                                                            ('tradingpartner_id', '!=', False),
                                                            ('edi_status', 'in', ['draft', 'pending'])])

    def _get_export_name(self):
        self.ensure_one()
        return self.op_type
