from lxml import etree
from odoo import fields, models, api


class BaseInherit(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(BaseInherit, self).get_view(view_id=view_id, view_type=view_type, options=options)
        if (res and view_type == 'form'
                and self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user')):
            relational_fields = [field for field in self._fields.values() if
                                 field.type in ['many2one', 'one2many', 'one2many']]
            arch = res.get('arch', {})
            tree = etree.fromstring(arch)
            for field in relational_fields:
                for node in tree.xpath(f'//field[@name="{field.name}"]'):
                    node.set('options', "{'create': false, 'create_edit': false, 'search_more': "
                                        "false, 'no_open': true}")
                    if field.type == 'one2many':
                        node.set('options', "{'create': true, 'create_edit': false, 'search_more': "
                                            "false, 'open': false}")
                        sub_relational_fields = [sub for sub in self.env[field.comodel_name]._fields.values() if
                                                 sub.type in ['many2one', 'one2many', 'many2many']]
                        for sub_field in sub_relational_fields:
                            for sub_element in node.xpath(f'//field[@name="{sub_field.name}"]'):
                                sub_element.set('options', "{'create': true, 'create_edit': true, 'search_more': "
                                                           "false, 'no_open': true}")

            res['arch'] = etree.tostring(tree)

        return res
