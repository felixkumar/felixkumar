from odoo import api, fields, models

class SyncDocumentType(models.Model):
    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
        ('import_so_xml', '850 - Import Order (SPS Commerce XML)')
    ], ondelete={'import_so_xml': 'cascade'})
