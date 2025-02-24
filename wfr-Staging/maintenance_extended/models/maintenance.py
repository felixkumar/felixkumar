# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    asset_tag = fields.Char(string="Asset Tag")
    maintenance_image = fields.Image(string="Images")
    move_id = fields.Many2one(comodel_name='account.move', string='Invoice/Bill')
    maintenance_employee_ids = fields.Many2many('hr.employee', string="Employee", copy=False)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        domain = ['|', ('name', operator, name),
                  ('partner_ref', operator, name)
                  ]
        args += domain
        pro_types = self.search(args, limit=limit)
        return pro_types.name_get()

    def name_get(self):
        result=[]
        res = super(MaintenanceEquipment, self).name_get()
        if self._context.get('is_asset_record'):
            for record in self:
                result.append((record.id, '[' + str(record.partner_ref) + ']' + record.name))
            return result
        return res

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         if record.partner_ref:
    #             result.append((record.id, '[' + str(record.partner_ref) + ']' + record.name +  '/' + record.serial_no))
    #     return result


    
class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'
    _description = 'Maintenance Request'

    vendor_work_order = fields.Char(string="Vendor Work Order #")
    move_id = fields.Many2one(comodel_name='account.move', string='Invoice/Bill')

