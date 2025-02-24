import json
from os.path import join as join_path

from odoo import models
from odoo.modules import get_module_path


class EdiMapping(models.Model):
    _inherit = 'edi.mapping'
    
    def configure(self):
        picking_import_mappings = self.filtered_domain([('sync_action_doc_type', '=', 'import_picking_xml')])
        other_mappings = self - picking_import_mappings
        module_path = get_module_path('edi_import_stock')
        for sale_import_mapping in picking_import_mappings:
            sale_import_mapping._configure_import_from_json_file(join_path(module_path, 'data/stock_picking_mappings.json'))
        super(EdiMapping, other_mappings).configure()
        return self
