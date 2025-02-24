from odoo import api, fields, models

from datetime import datetime

DOCUMENT_ID_FORMAT = '%Y%m%d%H%M%S'

class Partner(models.Model):
    _inherit = 'res.partner'

    outbound_edi_inventory = fields.Boolean(string='Outbound 846 Inventory',
                                        help='Whether the contact sends outbound 846 Inventory Advice to the EDI.')

    edi_inventory_inquiry_product_line_ids = fields.Many2many(string='EDI inventory inquiry Products', 
                                        comodel_name='product.template', 
                                        help='Inventory info for products in this list will be sent to to partner' )

    edi_tset_purpose_code = fields.Char('edi_tset_purpose_code')
    edi_report_type_code = fields.Char('edi_report_type_code')
    edi_inventory_date = fields.Char('edi_inventory_date')
    edi_inventory_time = fields.Char('edi_inventory_time')
    edi_vendor = fields.Char('edi_vendor')
    edi_status = fields.Char('edi_status')
    edi_date = fields.Datetime('edi_date')
    edi_address_type_code = fields.Selection([
        ('RL', 'Reporting Location')],
        string='EDI Address Type Code',
        help='Code identifying an organizational entity, a physical location, property, or an individual<')
    
    edi_document_id = fields.Char('EDI Document ID', compute='_get_edi_document_id')
    edi_total_amount = fields.Float('EDI Total Amount', compute='_compute_total_amount')
    edi_total_line_item_number = fields.Integer('EDI Total Line Item Number', compute='_compute_total_line_item_number')
    edi_total_quantity = fields.Integer('EDI Total Quantity', compute='_compute_total_quantity')

    @api.depends('edi_inventory_inquiry_product_line_ids')
    def _compute_total_amount(self):
        for partner in self:
            partner.edi_total_amount = sum(partner.edi_inventory_inquiry_product_line_ids.mapped('list_price'))

    @api.depends('edi_inventory_inquiry_product_line_ids')
    def _compute_total_line_item_number(self):
        for partner in self:
            partner.edi_total_line_item_number = len(partner.edi_inventory_inquiry_product_line_ids)

    @api.depends('edi_inventory_inquiry_product_line_ids')
    def _compute_total_quantity(self):
        for partner in self:
            partner.edi_total_quantity = sum(partner.edi_inventory_inquiry_product_line_ids.mapped('qty_available'))


    def export_inventory_advice_to_edi(self):
        base_edi = self.env['edi.sync.action']
        sync_action = base_edi.search([('doc_type_id.doc_code', '=', 'export_inventory_xml')], limit=1)
        if sync_action:
            base_edi._do_doc_sync_cron(sync_action_id=sync_action, records=self)
            

    def _get_edi_partner(self):
        self.ensure_one()
        return self
    
    def _get_edi_document_id(self): 
        for partner in self:
            partner.edi_document_id = datetime.today().strftime(DOCUMENT_ID_FORMAT)

    def get_edi_name(self):
        self.ensure_one()
        return self.trading_partnerid
