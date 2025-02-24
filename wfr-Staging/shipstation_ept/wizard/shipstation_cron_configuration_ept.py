from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7 * interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


class ShipstationCronConfigurationEpt(models.TransientModel):
    _name = "shipstation.cron.configuration.ept"
    _description = "Shipstation Cron Configuration"

    # Auto cron for Export Order
    shipstation_instance_id = fields.Many2one("shipstation.instance.ept", string="Shipstation Instance")
    shipstaion_order_auto_export = fields.Boolean('Export Order', default=False,
                                                  help="Check if you want to automatically Export Orders To Shipstation")
    shipstation_export_order_interval_number = fields.Integer('Interval Number for Export Order',
                                                              help="Repeat every x.", default=1)
    shipstation_export_order_interval_type = fields.Selection([('minutes', 'Minutes'), ('hours', 'Hours'),
                                                               ('days', 'Days'), ('weeks', 'Weeks'),
                                                               ('months', 'Months')], 'Interval Unit for Export Order')
    shipstation_export_order_next_execution = fields.Datetime('Next Execution for Export Order',
                                                              help='Next Execution for Export Order')
    shipstation_export_order_user_id = fields.Many2one('res.users', string="User for Export Order",
                                                       help='User for Export Order',
                                                       default=lambda self: self.env.user)
    # Cron for Validate Order
    shipstaion_validate_order = fields.Boolean('Validate Order', default=False,
                                               help="Check if you want to automatically Validate Orders")
    shipstation_validate_order_interval_number = fields.Integer('Interval Number for Validate Order',
                                                                help="Repeat every x.", default=1)
    shipstation_validate_order_interval_type = fields.Selection([('minutes', 'Minutes'), ('hours', 'Hours'),
                                                                 ('days', 'Days'), ('weeks', 'Weeks'),
                                                                 ('months', 'Months')],
                                                                'Interval Unit for Validate Order')
    shipstation_validate_order_next_execution = fields.Datetime('Next Execution for Validate Order',
                                                                help='Next Execution for Validate Order')
    shipstation_validate_order_user_id = fields.Many2one('res.users', string="User for Validate Order",
                                                         help='User for Validate Order',
                                                         default=lambda self: self.env.user)
    @api.onchange("shipstation_instance_id")
    def onchange_shipstation_instance_id(self):
        instance = self.shipstation_instance_id
        self.update_export_order_cron_field(instance)
        self.update_validate_order_cron_field(instance)

    def save(self):
        instance = self.shipstation_instance_id
        self.setup_shipstation_export_order_cron(instance)
        self.setup_shipstation_validate_order_cron(instance)

    def update_export_order_cron_field(self, instance):
        """
        :return:
        """
        try:
            export_order_cron_exist = instance and self.env.ref(
                'shipstation_ept.ir_cron_shipstation_auto_export_order_instance_%d' % instance.id)
        except:
            export_order_cron_exist = False
        if export_order_cron_exist:
            self.shipstaion_order_auto_export = export_order_cron_exist.active or False
            self.shipstation_export_order_interval_number = export_order_cron_exist.interval_number or 1
            self.shipstation_export_order_interval_type = export_order_cron_exist.interval_type or False
            self.shipstation_export_order_next_execution = export_order_cron_exist.nextcall or False
            self.shipstation_export_order_user_id = export_order_cron_exist.user_id.id or False

    def setup_shipstation_export_order_cron(self, instance):
        """
        :return:
        """
        try:
            cron_exist = self.env.ref(
                'shipstation_ept.ir_cron_shipstation_auto_export_order_instance_%d' % instance.id)
        except:
            cron_exist = False
        if self.shipstaion_order_auto_export:
            nextcall = datetime.now() + _intervalTypes[self.shipstation_export_order_interval_type](
                self.shipstation_export_order_interval_number)
            vals = self.prepare_val_for_cron(self.shipstation_export_order_interval_number or 1,
                                             self.shipstation_export_order_interval_type,
                                             self.shipstation_export_order_user_id)
            vals.update(
                {'nextcall': self.shipstation_export_order_next_execution or nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                 'code': "model.export_to_shipstation_cron(ctx={'shipstation_instance_id':%d})" % instance.id,
                 })
            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    core_cron = self.env.ref("shipstation_ept.ir_cron_shipstation_auto_export_order")
                except:
                    core_cron = False
                name = instance.name + ' : ' + core_cron.name
                vals.update({'name': name})
                new_cron = core_cron.copy(default=vals)
                name = 'ir_cron_shipstation_auto_export_order_instance_%d' % (instance.id)
                self.create_ir_module_data_for_export(name, new_cron)
        else:
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def update_validate_order_cron_field(self, instance):
        """
        :return:
        """
        try:
            validate_order_cron_exist = instance and self.env.ref(
                'shipstation_ept.ir_cron_shipstation_auto_validate_order_instance_%d' % instance.id)
        except:
            validate_order_cron_exist = False
        if validate_order_cron_exist:
            self.shipstaion_validate_order = validate_order_cron_exist.active or False
            self.shipstation_validate_order_interval_number = validate_order_cron_exist.interval_number or 1
            self.shipstation_validate_order_interval_type = validate_order_cron_exist.interval_type or False
            self.shipstation_validate_order_next_execution = validate_order_cron_exist.nextcall or False
            self.shipstation_validate_order_user_id = validate_order_cron_exist.user_id.id or False

    def setup_shipstation_validate_order_cron(self, instance):
        """
        :return:
        """
        try:
            cron_exist = self.env.ref(
                'shipstation_ept.ir_cron_shipstation_auto_validate_order_instance_%d' % instance.id)
        except:
            cron_exist = False
        if self.shipstaion_validate_order:
            nextcall = datetime.now() + _intervalTypes[self.shipstation_validate_order_interval_type](
                self.shipstation_validate_order_interval_number)
            vals = self.prepare_val_for_cron(self.shipstation_validate_order_interval_number or 1,
                                             self.shipstation_validate_order_interval_type,
                                             self.shipstation_validate_order_user_id)
            vals.update(
                {'nextcall': self.shipstation_validate_order_next_execution or nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                 'code': "model.auto_validate_delivery_order(ctx={'shipstation_instance_id':%d})" % instance.id,
                 })
            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    core_cron = self.env.ref("shipstation_ept.ir_cron_shipstation_auto_validate_order")
                except:
                    core_cron = False
                name = instance.name + ' : ' + core_cron.name
                vals.update({'name': name})
                new_cron = core_cron.copy(default=vals)
                name = 'ir_cron_shipstation_auto_validate_order_instance_%d' % (instance.id)
                self.create_ir_module_data_for_export(name, new_cron)
        else:
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def create_ir_module_data_for_export(self, name, new_cron):
        self.env['ir.model.data'].create({'module': 'shipstation_ept',
                                          'name': name,
                                          'model': 'ir.cron',
                                          'res_id': new_cron.id,
                                          'noupdate': True})

    def prepare_val_for_cron(self, interval_number, interval_type, user_id):
        vals = {'active': True,
                'interval_number': interval_number,
                'interval_type': interval_type,
                'user_id': user_id.id if user_id else False}
        return vals
