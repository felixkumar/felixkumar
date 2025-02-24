from lxml import etree
from odoo import fields, models, api


class FreightIBLInherit(models.Model):
    _inherit = 'freight.freight'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(FreightIBLInherit, self).get_view(view_id=view_id, view_type=view_type, options=options)

        if res and self.env.context.get('is_outbound', False) and self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            arch = res.get('arch', {})
            element = etree.fromstring(arch)
            et = etree.ElementTree(element=element)
            root = et.getroot()
            root.set('create', "false")
            root.set('edit', "false")
            arch = etree.tostring(element)
            res['arch'] = arch
        return res

    def _get_mail_thread_data(self, request_list):
        res = super(FreightIBLInherit, self)._get_mail_thread_data(request_list)
        if res and self.is_outbound and self.env.user.has_group(
                'user_warehouse_restriction.user_carote_restriction_group_user'):
            res['hasWriteAccess'] = False
        return res

    @api.model
    def default_get(self, fields_list):
        res = super(FreightIBLInherit, self).default_get(fields_list)
        if not self.is_outbound and self.env.user.has_group(
                'user_warehouse_restriction.user_carote_restriction_group_user'):
            carote_company_id = self.env['res.partner'].search([("name", "=", "Carote USA, LLC")], limit=1)
            warefor_warehouse_id = self.env['stock.warehouse'].search([('name', '=', "Warefor - Unit 1")], limit=1)
            res['import_id'] = carote_company_id.id
            res['partner_id'] = carote_company_id.id
        return res
