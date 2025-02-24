import json
from os.path import join as join_path

from odoo import models
from odoo.modules import get_module_path


class EdiMapping(models.Model):
    _inherit = 'edi.mapping'
    
    def configure(self):
        sale_import_mappings = self.filtered_domain([('sync_action_doc_type', '=', 'export_sale_acknowledgement_xml')])
        other_mappings = self - sale_import_mappings
        module_path = get_module_path('edi_export_sale_ack')
        for sale_import_mapping in sale_import_mappings:
            sale_import_mapping._configure_export_from_json(join_path(module_path, 'data/sale_order_ack_mappings.json'))
        super(EdiMapping, other_mappings).configure()
        return self
