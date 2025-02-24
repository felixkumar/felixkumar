# import json

# from lxml import etree
from odoo import fields, models, api


class ProductTemplateInherited(models.Model):
    _inherit = 'product.template'

    can_edit = fields.Boolean("User can Edit", compute='compute_can_edit', default=True)

    def fields_get(self, allfields=None, attributes=None):
        res = super(ProductTemplateInherited, self).fields_get(allfields, attributes)
        if res.get('categ_id', False) and self.env.user.has_group(
                'user_warehouse_restriction.user_carote_restriction_group_user'):
            categ_ids = self.env.user.allowed_product_category_ids.ids
            if categ_ids:
                res['categ_id']['domain'] = ['|', ('id', 'in', categ_ids), ('id', 'child_of', categ_ids)]
        return res

    @api.model
    def default_get(self, fields_list):
        res = super(ProductTemplateInherited, self).default_get(fields_list)
        if self.env.user.has_group(
                'user_warehouse_restriction.user_carote_restriction_group_user'):
            categ_id = self.env.user.allowed_product_category_ids[0]
            if categ_id:
                res['categ_id'] = categ_id.id
        return res

    @api.depends('create_uid')
    def compute_can_edit(self):
        for res in self:
            if self.env.user.has_group(
                    'user_warehouse_restriction.user_carote_restriction_group_user') and res.create_uid.id != self.env.uid:
                res.can_edit = False
            else:
                res.can_edit = True

    # The below code can be used to add attrs to all fields in a view

    # @api.model
    # def get_view(self, view_id=None, view_type='form', **options):
    #     res = super(ProductTemplateInherited, self).get_view(view_id=view_id, view_type=view_type, options=options)
    #
    #     if res and view_type == 'form' and self.env.user.has_group(
    #             'user_warehouse_restriction.user_carote_restriction_group_user'):
    #         all_fields = [field for field in self._fields.values()]
    #         arch = res.get('arch', {})
    #         tree = etree.fromstring(arch)
    #         for field in all_fields:
    #             for node in tree.xpath(f'//field[@name="{field.name}"]'):
    #                 if node.attrib and node.attrib.get('modifiers', False):
    #                     mod = json.loads(node.attrib['modifiers'])
    #                     mod['readonly'] = [('can_edit', '=', False)]
    #                     node.attrib['modifiers'] = json.dumps(mod)
    #                 else:
    #                     mod = {'readonly': [('can_edit', '=', False)]}
    #                     node.attrib['modifiers'] = json.dumps(mod)
    #                     # node.set('modifiers', "{'readonly': [('can_edit', '=', False)]}")
    #         res['arch'] = etree.tostring(tree)
    #     return res
