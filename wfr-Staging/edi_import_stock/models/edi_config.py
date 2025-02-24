from odoo import api, fields, models

class SyncDocumentType(models.Model):
    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
        ('import_picking_xml', '856 - Import Picking (SPS Commerce XML)')
    ], ondelete={'import_picking_xml': 'cascade'})
