from lxml import etree
from odoo import models, api


class StockQuantInherit(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(StockQuantInherit, self).get_view(view_id=view_id, view_type=view_type, options=options)

        if res and self.env.user.has_group(
                'user_warehouse_restriction.user_carote_restriction_group_user'):
            arch = res.get('arch', {})
            element = etree.fromstring(arch)
            et = etree.ElementTree(element=element)
            root = et.getroot()
            root.set('create', "false")
            root.set('edit', "false")
            arch = etree.tostring(element)
            res['arch'] = arch
        return res
