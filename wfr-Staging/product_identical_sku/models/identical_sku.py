from odoo import fields, models, api, _


class IdenticalSku(models.Model):
    _name = 'identical.sku'
    _description = 'Identical SKUs'
    _order = 'product_id asc'

    name = fields.Char(string="Marketplace SKU")
    marketplace_id = fields.Many2one(comodel_name="edi.customer.store", string="Marketplace")
    is_third_party = fields.Boolean(string="Fulfilled by 3rd Party")
    product_id = fields.Many2one(comodel_name="product.template", string="Product")
    is_prime = fields.Boolean(string="Is Prime?")
    original_sku = fields.Char(string="Parent SKU", related='product_id.default_code')
    location_ids = fields.One2many(comodel_name='identical.sku.locations', inverse_name='sku_id', string='Locations')

    @api.onchange('name')
    def _onchange_sku(self):
        if not self.name:
            return

        domain = [('name', '=ilike', self.name)]
        if self.id:
            domain.append(('id', '!=', self.id))

        if self.env['identical.sku'].search(domain, limit=1):
            return {'warning': {
                'title': _("Note:"),
                'message': _("The SKU '%s' already exists.", self.name),
            }}
