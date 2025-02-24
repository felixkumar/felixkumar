from odoo import api, fields, models

class SyncDocumentType(models.Model):
    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
        ('export_inventory_inquiry_xml', '846 - Inventory Inquiry (SPS Commerce XML)')
    ], ondelete={'export_inventory_inquiry_xml': 'cascade'})



class EdiSyncAction(models.Model):
    _inherit = 'edi.sync.action'

    def _get_documents_to_export(self):
        self.ensure_one()
        if self.doc_type_id.doc_code == 'export_inventory_inquiry_xml':
            return self.env['res.partner'].sudo().search([('outbound_edi_inventory', '=', True)])
        else:
            return super()._get_documents_to_export()


