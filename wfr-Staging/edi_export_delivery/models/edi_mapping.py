import json
from os.path import join as join_path

from odoo import models
from odoo.modules import get_module_path


class EdiMapping(models.Model):
    _inherit = 'edi.mapping'
    
    def configure(self):
        inventory_export_mappings = self.filtered_domain([('sync_action_doc_type', '=', 'export_shipment_xml')])
        other_mappings = self - inventory_export_mappings
        module_path = get_module_path('edi_export_delivery')
        for inventory_export_mapping in inventory_export_mappings:
            inventory_export_mapping._configure_export_from_json(join_path(module_path, 'data/delivery_mapping.json'))
        super(EdiMapping, other_mappings).configure()
        return self
