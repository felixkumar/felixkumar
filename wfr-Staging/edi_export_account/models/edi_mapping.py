from os.path import join as join_path

from odoo import models
from odoo.modules import get_module_path


class EdiMapping(models.Model):
    _inherit = 'edi.mapping'

    def configure(self):
        invoice_export_mappings = self.filtered_domain([('sync_action_doc_type', '=', 'export_invoice_xml')])
        other_mappings = self - invoice_export_mappings
        module_path = get_module_path('edi_export_account')
        for sale_import_mapping in invoice_export_mappings:
            sale_import_mapping._configure_export_from_json(join_path(module_path, 'data/account_move_mappings.json'))
        super(EdiMapping, other_mappings).configure()
        return self
