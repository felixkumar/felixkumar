import json
from os.path import join as join_path

from odoo import models
from odoo.modules import get_module_path


class EdiMapping(models.Model):
    _inherit = 'edi.mapping'
    
    def configure(self):
        module_path = get_module_path('edi_export_inventory')
        inventory_export_mappings = self.filtered_domain([('sync_action_doc_type', '=', 'export_inventory_inquiry_xml')])
        other_mappings = self - inventory_export_mappings
        for inventory_export_mapping in inventory_export_mappings:
            inventory_export_mapping._configure_export_from_json(join_path(module_path, 'data/inventory_mapping.json'))
        super(EdiMapping, other_mappings).configure()
        return self
