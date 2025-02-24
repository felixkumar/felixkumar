from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    outbound_edi_inventory_partners = fields.Many2many(string='846 Partners', comodel_name='res.partner', relation='product_template_res_partner_edi_rel', column1='template_id', column2='partner_id', domain='[("outbound_edi_inventory", "=", True), ("is_company","=",True)]')

    edi_consumer_package_code = fields.Char('EDI Consumer Package Code', 
                                        help='Consumer level or customer unit product identification number')
    edi_price_type_id_code = fields.Char('EDI Price type ID Code', 
                                        help='Code identifying the type of price')
    edi_expiration_date = fields.Date('EDI Expiration Date', 
                                        help='Product Expiration Date')

    
    edi_location = fields.Char('EDI Location', compute='_compute_edi_location', store=False)

    def _compute_edi_location(self):
        for product in self:
            location_names = [quant.location_id.display_name for quant in self.product_variant_id.stock_quant_ids if quant.location_id.usage == 'internal']
            product.edi_location = location_names[0] if location_names else 'Stock'
