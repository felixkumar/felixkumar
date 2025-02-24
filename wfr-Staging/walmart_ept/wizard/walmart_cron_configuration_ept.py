from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

from odoo import models, fields, api, _

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7 * interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


class WalmartCronConfigurationEPT(models.TransientModel):
    _name = "walmart.cron.configuration.ept"
    _description = "Walmart Cron Configuration"

    def _get_walmart_marketplace(self):
        return self.env.context.get('walmart_marketplace_id', False)

    walmart_marketplace_id = fields.Many2one('walmart.marketplace.ept',
                                             string="Walmart Marketplace",
                                             default=_get_walmart_marketplace,
                                             help="Select Walmart Marketplace")

    # Auto Import Walmart Orders ?
    auto_import_walmart_orders = fields.Boolean(
        "Auto Import Walmart Orders ?", help='It will automatically \
        import orders by executing cron at a particular time interval.')

    auto_import_walmart_orders_interval_number = fields.Integer(
        help="Auto Import Order Repeat every x.")
    auto_import_walmart_orders_interval_type = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'),
         ('months', 'Months')],
        'Auto Import Walmart Orders Interval Unit')
    auto_import_walmart_orders_next_execution = fields.Datetime(
        help='Next execution time')
    auto_import_walmart_orders_user_id = fields.Many2one("res.users",
                                                         string="Walmart Auto Import Orders User")

    # Auto import walmart WFS Order ?
    auto_import_walmart_wfs_orders = fields.Boolean(
        "Auto Import Walmart WFS Orders ?", help='It will automatically \
            import WFS orders by executing cron at a particular time interval.')

    auto_import_walmart_wfs_orders_interval_number = fields.Integer(
        help="Auto Import WFS Order Repeat every x.")

    auto_import_walmart_wfs_orders_interval_type = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'),
         ('months', 'Months')],
        'Auto Import Walmart Order Interval Unit')

    auto_import_walmart_wfs_orders_next_execution = fields.Datetime(
        help='Next execution time')

    auto_import_walmart_wfs_orders_user_id = fields.Many2one("res.users",
                                                             string="Walmart Auto Import Order User")

    # Auto import walmart WFS inventory ?
    auto_import_walmart_wfs_inventory = fields.Boolean(
        "Auto Import Walmart WFS Inventory ?", help='It will automatically \
                import WFS Inventory by executing cron at a particular time interval.')

    auto_import_walmart_wfs_inventory_interval_number = fields.Integer(
        help="Auto Import WFS Inventory Repeat every x.")

    auto_import_walmart_wfs_inventory_interval_type = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'),
         ('months', 'Months')],
        'Auto Import Walmart Inventory Interval Unit')

    auto_import_walmart_wfs_inventory_next_execution = fields.Datetime(
        help='Next execution time')

    auto_import_walmart_wfs_inventory_user_id = fields.Many2one("res.users",
                                                                string="Walmart Auto Import Inventory User")

    # Auto Inventory Export ?
    walmart_stock_auto_export = fields.Boolean(string="Auto Inventory Export ?")
    walmart_update_stock_interval_number = fields.Integer('Update Stock Interval Number',
                                                          help="Update Stock Repeat every x.")
    walmart_update_stock_interval_type = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'),
         ('months', 'Months')], 'Update Stock Interval Unit')
    walmart_update_stock_next_execution = fields.Datetime('Next Execution of Update Stock',
                                                          help='Next execution time')
    walmart_stock_update_user_id = fields.Many2one('res.users', string="Stock Update By User",
                                                   help='User')

    # Auto Order Update ?
    walmart_order_auto_update = fields.Boolean(string="Auto Update Order Status ?")
    walmart_order_update_interval_number = fields.Integer(
        'Update Order Interval Number', help="Update Order Status Repeat every x.")
    walmart_order_update_interval_type = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'),
         ('months', 'Months')], 'Update Order Interval Unit')
    walmart_order_update_next_execution = fields.Datetime('Next Execution of Update Order',
                                                          help='Next execution time')
    walmart_order_status_update_user_id = fields.Many2one('res.users',
                                                          string="Update Order Status By User",
                                                          help='User')

    # Auto Get Item Details
    walmart_auto_create_item_report_request = fields.Boolean(string="Auto Create Item Report Request")
    walmart_auto_create_item_report_request_interval_number = fields.Integer(
        'Auto Create Item Report Interval Number',
        help="Get Item Report Repeat every x.")
    walmart_auto_create_item_report_request_interval_type = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'),
         ('months', 'Months')], 'Create Item Report Interval Unit')
    walmart_auto_create_item_report_request_next_execution = fields.Datetime(
        'Auto Create Item Report Next Execution Time',
        help='Next execution time')
    walmart_auto_create_item_report_request_user_id = fields.Many2one('res.users',
                                                           string="Auto Create Item Report By User",
                                                           help='User')
    walmart_auto_process_item_report = fields.Boolean(string="Auto Process Item Details")
    walmart_auto_process_item_report_interval_number = fields.Integer(
        'Auto Process Item Report Interval Number',
        help="Get Item Report Repeat every x.")
    walmart_auto_process_item_report_interval_type = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'),
         ('months', 'Months')], 'Process Item Report Interval Unit')
    walmart_auto_process_item_report_next_execution = fields.Datetime(
        'Auto Process Item Report Next Execution Time',
        help='Next execution time')
    walmart_auto_process_item_report_user_id = fields.Many2one('res.users',
                                                           string="Auto Process Item Report By User",
                                                           help='User')
    update_product_image = fields.Boolean("Auto Update Product Image", default=False)
    create_product_inventory = fields.Boolean("Auto Create Product Inventory", default=False)
    location_id = fields.Many2one('stock.location', string="Source Location",
                                  domain=[('usage', '=', 'internal')])

    # Auto Send invoice Email ?
    walmart_auto_send_invoice = fields.Boolean("Auto Send invoice Email ?")
    walmart_send_invoice_interval_number = fields.Integer(
        'Auto Send Invoice Interval Number', help="Auto Send Invoice Mail  Repeat every x.")
    walmart_send_invoice_interval_type = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'),
         ('months', 'Months')], 'Update Send Invoice Interval Unit')
    walmart_send_invoice_next_execution = fields.Datetime('Next Execution of Send Invoice',
                                                          help='Next execution time')
    walmart_send_invoice_update_user_id = fields.Many2one('res.users',
                                                          string="Update Auto Send Invoice By User",
                                                          help='User')

    # Auto Send Refund invoice Email ?
    walmart_auto_send_refund_invoice = fields.Boolean("Auto Send Refund invoice Email ?")
    walmart_refund_invoice_send_interval_number = fields.Integer(
        'Auto Send Refund Invoice Interval Number',
        help="Auto Send Invoice Mail  Repeat every x.")
    walmart_refund_invoice_send_interval_type = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'),
         ('months', 'Months')], 'Update Send Refund Invoice Interval Unit')
    walmart_refund_invoice_send_next_execution = fields.Datetime(
        'Next Execution of Refund Invoice Send',
        help='Next execution time')
    walmart_refund_invoice_send_update_user_id = fields.Many2one(
        'res.users', string="Update Send Refund Invoice By User")

    # Auto import walmart Reconciliation report ?
    auto_import_walmart_reconciliation_report = fields.Boolean(
        string="Auto Import Walmart Reconciliation Report ?",
        help='It will automatically import reconciliation report by executing cron at a particular time interval.')
    auto_import_walmart_reconciliation_report_interval_number = fields.Integer(
        help="Auto Import Reconciliation Report Repeat every x.")
    auto_import_walmart_reconciliation_report_interval_type = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'),
         ('weeks', 'Weeks'), ('months', 'Months')],
        string='Auto Import Walmart Reconciliation Report IntervalUnit')
    auto_import_walmart_reconciliation_report_next_execution = fields.Datetime(help='Next execution time')
    auto_import_walmart_reconciliation_report_user_id = fields.Many2one(
        "res.users", string="Walmart Auto Import Reconciliation Report User")

    @api.constrains("auto_import_walmart_orders_interval_number", "walmart_update_stock_interval_number",
                    "walmart_order_update_interval_number", "walmart_auto_create_item_report_request_interval_number",
                    "auto_import_walmart_wfs_orders_interval_number", "auto_import_walmart_wfs_inventory_interval_number",
                    "walmart_auto_process_item_report_interval_number", "auto_import_walmart_reconciliation_report_interval_number")
    def check_interval_time(self):
        """
        It does not let set the cron execution time to Zero.
        @author: Nikul Alagiya on Date 25-Jan-2022.
        """
        for record in self:
            is_zero = False
            if record.auto_import_walmart_orders and record.auto_import_walmart_orders_interval_number <= 0:
                is_zero = True
            if record.auto_import_walmart_wfs_orders and record.auto_import_walmart_wfs_orders_interval_number <= 0:
                is_zero = True
            if record.auto_import_walmart_wfs_inventory and record.auto_import_walmart_wfs_inventory_interval_number <= 0:
                is_zero = True
            if record.walmart_stock_auto_export and record.walmart_update_stock_interval_number <= 0:
                is_zero = True
            if record.walmart_order_auto_update and record.walmart_order_update_interval_number <= 0:
                is_zero = True
            if record.walmart_auto_create_item_report_request and record.walmart_auto_create_item_report_request_interval_number <= 0:
                is_zero = True
            if record.walmart_auto_process_item_report and record.walmart_auto_process_item_report_interval_number <= 0:
                is_zero = True
            if record.auto_import_walmart_reconciliation_report and \
                    record.auto_import_walmart_reconciliation_report_interval_number <= 0:
                is_zero = True
            if is_zero:
                raise ValidationError(_("Cron Execution Time can't be set to 0(Zero). "))

    @api.onchange('walmart_marketplace_id')
    def onchange_walmart_marketplace_id(self):
        """
        Set cron field value while open the wizard for cron configuration from the instance form view.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 28/01/2022.
        """
        if self.walmart_marketplace_id:
            marketplace_id = self.walmart_marketplace_id

            self.walmart_stock_auto_export = marketplace_id.stock_auto_export or False
            self.walmart_order_auto_update = marketplace_id.order_auto_update or False
            self.auto_import_walmart_orders = marketplace_id.auto_import_walmart_orders or False
            self.auto_import_walmart_wfs_orders = marketplace_id.auto_import_walmart_wfs_orders or False
            self.auto_import_walmart_wfs_inventory = marketplace_id.auto_import_walmart_wfs_inventory or False
            self.walmart_auto_create_item_report_request = marketplace_id.auto_create_item_report_request or False
            self.walmart_auto_process_item_report = marketplace_id.auto_process_item_report or False
            self.walmart_auto_send_invoice = marketplace_id.auto_send_invoice or False
            self.walmart_auto_send_refund_invoice = marketplace_id.auto_send_refund_invoice or False
            self.update_product_image = marketplace_id.update_product_image or False
            self.create_product_inventory = marketplace_id.create_product_inventory or False
            self.location_id = marketplace_id.location_id.id or False
            self.auto_import_walmart_reconciliation_report = marketplace_id.auto_import_walmart_reconciliation_report or False

            self.update_export_inventory_cron_field(marketplace_id)
            self.update_order_status_cron_field(marketplace_id)
            self.import_walmart_order_cron_field(marketplace_id)
            self.create_item_report_request_cron_field(marketplace_id)
            self.process_item_report_cron_field(marketplace_id)
            self.import_walmart_wfs_order_cron_field(marketplace_id)
            self.import_walmart_wfs_inventory_cron_field(marketplace_id)
            self.auto_send_invoice_via_email_cron_field(marketplace_id)
            self.import_walmart_reconciliation_report_cron_field(marketplace_id)

    def update_export_inventory_cron_field(self, instance):
        """
        Set export Inventory cron fields value while open the wizard for cron configuration from the instance form view.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 28/01/2022.
        """
        # Auto Export Inventory
        try:
            inventory_cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_export_inventory_instance_%d' % instance.id,
                raise_if_not_found=False)

        except:
            inventory_cron_exist = False
        if inventory_cron_exist:
            self.walmart_stock_auto_export = inventory_cron_exist.active or False
            self.walmart_update_stock_interval_number = inventory_cron_exist.interval_number
            self.walmart_update_stock_interval_type = inventory_cron_exist.interval_type
            self.walmart_update_stock_next_execution = inventory_cron_exist.nextcall
            self.walmart_stock_update_user_id = inventory_cron_exist.user_id.id

    def update_order_status_cron_field(self, instance):
        """
        Set update order status cron fields value while open the wizard for cron configuration from the instance form view.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 28/01/2022.
        """
        # Auto Update Order Status
        try:
            order_update_cron_exist = self.env.ref(
                'walmart_ept.ir_cron_update_order_status_instance_%d' % instance.id,
                raise_if_not_found=False)
        except:
            order_update_cron_exist = False
        if order_update_cron_exist:
            self.walmart_order_auto_update = order_update_cron_exist.active or False
            self.walmart_order_update_interval_number = order_update_cron_exist.interval_number
            self.walmart_order_update_interval_type = order_update_cron_exist.interval_type
            self.walmart_order_update_next_execution = order_update_cron_exist.nextcall
            self.walmart_order_status_update_user_id = order_update_cron_exist.user_id.id

    def import_walmart_order_cron_field(self, instance):
        """
        Set Import Walmart Orders cron fields value while open the wizard for cron configuration from the instance form view.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 28/01/2022.
        """
        # Auto Import Walmart Orders
        try:
            auto_import_walmart_orders_cron = \
                self.env.ref('walmart_ept.ir_cron_auto_import_walmart_orders_instance_%d' \
                             % instance.id, raise_if_not_found=False)
        except:
            auto_import_walmart_orders_cron = False
        if auto_import_walmart_orders_cron:
            self.auto_import_walmart_orders = auto_import_walmart_orders_cron.active or False
            self.auto_import_walmart_orders_next_execution = auto_import_walmart_orders_cron.nextcall
            self.auto_import_walmart_orders_interval_number = auto_import_walmart_orders_cron.interval_number
            self.auto_import_walmart_orders_interval_type = auto_import_walmart_orders_cron.interval_type
            self.auto_import_walmart_orders_user_id = auto_import_walmart_orders_cron.user_id.id

    def create_item_report_request_cron_field(self, instance):
        try:
            auto_create_item_report_request = \
                self.env.ref('walmart_ept.ir_cron_auto_create_item_report_request_%d' \
                             % instance.id, raise_if_not_found=False)
        except:
            auto_create_item_report_request = False
        if auto_create_item_report_request:
            self.walmart_auto_create_item_report_request = auto_create_item_report_request.active or False
            self.walmart_auto_create_item_report_request_interval_number = auto_create_item_report_request.interval_number
            self.walmart_auto_create_item_report_request_interval_type = auto_create_item_report_request.interval_type
            self.walmart_auto_create_item_report_request_next_execution = auto_create_item_report_request.nextcall
            self.walmart_auto_create_item_report_request_user_id = auto_create_item_report_request.user_id.id

    def process_item_report_cron_field(self, instance):
        try:
            auto_process_item_report = \
                self.env.ref('walmart_ept.ir_cron_auto_process_item_report_%d' \
                             % instance.id, raise_if_not_found=False)
        except:
            auto_process_item_report = False
        if auto_process_item_report:
            self.walmart_auto_process_item_report = auto_process_item_report.active or False
            self.walmart_auto_process_item_report_interval_number = auto_process_item_report.interval_number
            self.walmart_auto_process_item_report_interval_type = auto_process_item_report.interval_type
            self.walmart_auto_process_item_report_next_execution = auto_process_item_report.nextcall
            self.walmart_auto_process_item_report_user_id = auto_process_item_report.user_id.id

    def import_walmart_wfs_order_cron_field(self, instance):
        """
        Set Import Walmart WFS Orders cron fields value while open the wizard for cron configuration from the instance form view.
        @author: Yagnik Joshi @Emipro Technologies Pvt. Ltd on date 05/10/2022.
        """
        # Auto Import Walmart Orders
        try:
            auto_import_walmart_wfs_order_cron = \
                self.env.ref('walmart_ept.ir_cron_auto_import_walmart_wfs_orders_instance_%d' \
                             % instance.id, raise_if_not_found=False)
        except:
            auto_import_walmart_wfs_order_cron = False
        if auto_import_walmart_wfs_order_cron:
            self.auto_import_walmart_wfs_orders = auto_import_walmart_wfs_order_cron.active or False
            self.auto_import_walmart_wfs_orders_next_execution = auto_import_walmart_wfs_order_cron.nextcall
            self.auto_import_walmart_wfs_orders_interval_number = auto_import_walmart_wfs_order_cron.interval_number
            self.auto_import_walmart_wfs_orders_interval_type = auto_import_walmart_wfs_order_cron.interval_type
            self.auto_import_walmart_wfs_orders_user_id = auto_import_walmart_wfs_order_cron.user_id.id

    def import_walmart_reconciliation_report_cron_field(self, instance):
        """
        Define this method for update auto import reconciliation report scheduler fields.
        :param instance: walmart.marketplace.ept()
        :return:
        """
        try:
            # need to create first cron and then update here name
            auto_import_reconciliation_report_cron = self.env.ref(
                'walmart_ept.ir_cron_auto_import_walmart_reconciliation_report_instance_%d' %
                instance.id, raise_if_not_found=False)
        except:
            auto_import_reconciliation_report_cron = False
        if auto_import_reconciliation_report_cron:
            self.auto_import_walmart_reconciliation_report = auto_import_reconciliation_report_cron.active or False
            self.auto_import_walmart_reconciliation_report_next_execution = auto_import_reconciliation_report_cron.nextcall
            self.auto_import_walmart_reconciliation_report_interval_number = auto_import_reconciliation_report_cron.interval_number
            self.auto_import_walmart_reconciliation_report_interval_type = auto_import_reconciliation_report_cron.interval_type
            self.auto_import_walmart_reconciliation_report_user_id = auto_import_reconciliation_report_cron.user_id.id

    def import_walmart_wfs_inventory_cron_field(self, instance):
        """
            Set Import Walmart WFS Inventory cron fields value while open the wizard for cron configuration from the instance form view.
            @author: Yagnik Joshi @Emipro Technologies Pvt. Ltd on date 19/12/2022.
            """
        # Auto Import Walmart WFS Inventory
        try:
            auto_import_walmart_wfs_inventory_cron = \
                self.env.ref('walmart_ept.ir_cron_auto_import_walmart_wfs_inventory_instance_%d' \
                             % instance.id, raise_if_not_found=False)
        except:
            auto_import_walmart_wfs_inventory_cron = False
        if auto_import_walmart_wfs_inventory_cron:
            self.auto_import_walmart_wfs_inventory = auto_import_walmart_wfs_inventory_cron.active or False
            self.auto_import_walmart_wfs_inventory_next_execution = auto_import_walmart_wfs_inventory_cron.nextcall
            self.auto_import_walmart_wfs_inventory_interval_number = auto_import_walmart_wfs_inventory_cron.interval_number
            self.auto_import_walmart_wfs_inventory_interval_type = auto_import_walmart_wfs_inventory_cron.interval_type
            self.auto_import_walmart_wfs_inventory_user_id = auto_import_walmart_wfs_inventory_cron.user_id.id

    def auto_send_invoice_via_email_cron_field(self, instance):
        # Auto Send invoice via e-mail
        try:
            send_inv_cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_send_invoice_via_mail_%d' % instance.id,
                raise_if_not_found=False)
        except:
            send_inv_cron_exist = False
        if send_inv_cron_exist:
            self.walmart_auto_send_invoice = send_inv_cron_exist.active or False
            self.walmart_send_invoice_interval_number = send_inv_cron_exist.interval_number
            self.walmart_send_invoice_interval_type = send_inv_cron_exist.interval_type
            self.walmart_send_invoice_next_execution = send_inv_cron_exist.nextcall
            self.walmart_send_invoice_update_user_id = send_inv_cron_exist.user_id.id

    def save_cron_configuration(self):
        values = {}
        marketplace_id = self.walmart_marketplace_id
        if marketplace_id:
            values['auto_import_walmart_orders'] = self.auto_import_walmart_orders
            values['auto_import_walmart_wfs_orders'] = self.auto_import_walmart_wfs_orders
            values['auto_import_walmart_wfs_inventory'] = self.auto_import_walmart_wfs_inventory
            values['auto_create_item_report_request'] = self.walmart_auto_create_item_report_request
            values['auto_process_item_report'] = self.walmart_auto_process_item_report
            values['stock_auto_export'] = self.walmart_stock_auto_export or False
            values['auto_send_invoice'] = self.walmart_auto_send_invoice or False
            values['auto_send_refund_invoice'] = self.walmart_auto_send_refund_invoice or False
            values['order_auto_update'] = self.walmart_order_auto_update or False
            values['update_product_image'] = self.update_product_image or False
            values['create_product_inventory'] = self.create_product_inventory or False
            values['location_id'] = self.location_id.id or False
            values['auto_import_walmart_reconciliation_report'] = self.auto_import_walmart_reconciliation_report or False

            marketplace_id.write(values)
            self.setup_order_status_update_cron(marketplace_id)
            self.setup_update_stock_cron(marketplace_id)
            self.setup_walmart_import_order_cron(marketplace_id)
            self.setup_walmart_import_wfs_order_cron(marketplace_id)
            self.setup_walmart_import_wfs_inventory_cron(marketplace_id)
            self.setup_auto_create_item_report_request(marketplace_id)
            self.setup_auto_process_item_report(marketplace_id)
            self.setup_auto_send_invoice_via_email(marketplace_id)
            self.setup_auto_send_refund_invoice_via_email(marketplace_id)
            self.setup_walmart_import_reconciliation_report_cron(marketplace_id)
        if self._context.get('is_calling_from_onboarding_panel', False):
            if not marketplace_id:
                marketplace_id = self.walmart_marketplace_id
            if marketplace_id:
                action = self.env["ir.actions.actions"]._for_xml_id(
                    "walmart_ept.walmart_onboarding_confirmation_wizard_action")
                action['context'] = {'walmart_marketplace_id': marketplace_id.id}
                return action
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def setup_auto_import_order_cron(self, marketplace):
        if self.auto_import_walmart_orders:
            cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_import_walmart_orders_marketplace_%d' % (marketplace.id),
                raise_if_not_found=False)
            vals = {'active': True,
                    'interval_number': self.auto_import_walmart_orders_interval_number,
                    'interval_type': self.auto_import_walmart_orders_interval_type,
                    'nextcall': self.auto_import_walmart_orders_next_execution,
                    'user_id': self.auto_import_walmart_orders_user_id.id,
                    'code': "model.auto_import_walmart_orders_via_cron(marketplace_id=%d)" % (
                        marketplace.id)}
            if cron_exist:
                cron_exist.write(vals)
            else:
                import_order_cron = self.env.ref('walmart_ept.ir_cron_auto_import_walmart_orders',
                                                 raise_if_not_found=False)
                if not import_order_cron:
                    raise ValidationError(_(
                        'Core settings of Walmart are deleted, \
                        please upgrade Walmart module to back this settings.'))

                name = marketplace.name + ' : Auto Import Orders'
                vals.update({'name': name})
                new_cron = import_order_cron.copy(default=vals)
                self.env['ir.model.data'].create(
                    {'module': 'walmart_ept',
                     'name': 'ir_cron_auto_import_walmart_orders_marketplace_%d' % (
                         marketplace.id),
                     'model': 'ir.cron',
                     'res_id': new_cron.id,
                     'noupdate': True})
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_import_walmart_orders_marketplace_%d' % (
                        marketplace.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def setup_auto_import_wfs_order_cron(self, marketplace):
        if self.auto_import_walmart_wfs_orders:
            cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_import_walmart_wfs_orders_marketplace_%d' % (marketplace.id),
                raise_if_not_found=False)
            vals = {
                'active': True,
                'interval_number': self.auto_import_walmart_wfs_orders_interval_number,
                'interval_type': self.auto_import_walmart_wfs_orders_interval_type,
                'nextcall': self.auto_import_walmart_wfs_orders_next_execution,
                'user_id': self.auto_import_walmart_wfs_orders_user_id.id,
                'code': "model.with_context(wfs_order=True).auto_import_walmart_wfs_orders_via_cron(marketplace_id=%d)" % (marketplace.id)
            }
            if cron_exist:
                cron_exist.write(vals)
            else:
                import_wfs_order_cron = self.env.ref('walmart_ept.ir_cron_auto_import_walmart_wfs_orders',
                                                     raise_if_not_found=False)
                if not import_wfs_order_cron:
                    raise ValidationError(
                        _('Core settings of Walmart are deleted, \ please upgrade Walmart module to back this settings.'))

                name = marketplace.name + ' : Auto Import WFS Orders'
                vals.update({'name': name})
                new_cron = import_wfs_order_cron.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module': 'walmart_ept',
                    'name': 'ir_cron_auto_import_walmart_wfs_orders_marketplace_%d' % (marketplace.id),
                    'model': 'ir.cron',
                    'res_id': new_cron.id,
                    'noupdate': True
                })
        else:
            try:
                cron_exist = self.env.ref('walmart_ept.ir_cron_auto_import_walmart_wfs_orders_marketplace_%d' % (marketplace.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def setup_auto_import_wfs_inventory_cron(self, marketplace):
        if self.auto_import_walmart_wfs_inventory:
            cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_import_walmart_wfs_inventory_marketplace_%d' % (marketplace.id),
                raise_if_not_found=False)
            vals = {
                'active': True,
                'interval_number': self.auto_import_walmart_wfs_inventory_interval_number,
                'interval_type': self.auto_import_walmart_wfs_inventory_interval_type,
                'nextcall': self.auto_import_walmart_wfs_inventory_next_execution,
                'user_id': self.auto_import_walmart_wfs_inventory_user_id,
                'code': "model.auto_import_walmart_wfs_inventory_via_cron(marketplace_id=%d)" % (marketplace.id)
            }
            if cron_exist:
                cron_exist.write(vals)
            else:
                import_wfs_inventory_cron = self.env.ref('walmart_ept.ir_cron_auto_import_walmart_wfs_inventory',
                                                         raise_if_not_found=False)
                if not import_wfs_inventory_cron:
                    raise ValidationError(
                        _('Core settings of Walmart are deleted, \ please upgrade Walmart module to back this settings.'))
                name = marketplace.name + ' : Auto Import WFS inventory'
                vals.update({'name': name})
                new_cron = import_wfs_inventory_cron.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module': 'walmart_ept',
                    'name': 'ir_cron_auto_import_walmart_wfs_inventory_marketplace_%d' % (marketplace.id),
                    'model': 'ir.cron',
                    'res_id': new_cron.id,
                    'noupdate': True
                })
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_import_walmart_wfs_inventory_marketplace_%d' % (marketplace.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    # Cron Method Added By Harshit (Update Status, Update Stock)

    def setup_order_status_update_cron(self, instance):
        if self.walmart_order_auto_update:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_update_order_status_instance_%d' % (instance.id))
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.walmart_order_update_interval_type](
                self.walmart_order_update_interval_number)
            vals = {'active': True,
                    'interval_number': self.walmart_order_update_interval_number,
                    'interval_type': self.walmart_order_update_interval_type,
                    'nextcall': self.walmart_order_update_next_execution or nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': self.walmart_order_status_update_user_id.id,
                    'code': "model.auto_update_order_status_ept(instance_id=%d)" % (
                        instance.id)}

            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    update_order_cron = self.env.ref('walmart_ept.ir_cron_update_order_status')
                except:
                    update_order_cron = False
                if not update_order_cron:
                    raise ValidationError(_(
                        'Core settings of Walmart are deleted,\
                         please upgrade Walmart Odoo Connector module to back this settings.'))

                name = instance.name + ' : ' + update_order_cron.name
                vals.update({'name': name})
                new_cron = update_order_cron.copy(default=vals)
                self.env['ir.model.data'].create(
                    {'module': 'walmart_ept',
                     'name': 'ir_cron_update_order_status_instance_%d' % (
                         instance.id),
                     'model': 'ir.cron',
                     'res_id': new_cron.id,
                     'noupdate': True})
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_update_order_status_instance_%d' % (instance.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def setup_update_stock_cron(self, instance):
        if self.walmart_stock_auto_export:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_export_inventory_instance_%d' % (instance.id))
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.walmart_update_stock_interval_type](
                self.walmart_update_stock_interval_number)
            vals = {'active': True,
                    'interval_number': self.walmart_update_stock_interval_number,
                    'interval_type': self.walmart_update_stock_interval_type,
                    'nextcall': self.walmart_update_stock_next_execution or nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': self.walmart_stock_update_user_id.id,
                    'code': "model.auto_export_inventory_ept(instance_id=%d)" % (instance.id)}

            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    update_stock_cron = self.env.ref('walmart_ept.ir_cron_auto_export_inventory')
                except:
                    update_stock_cron = False
                if not update_stock_cron:
                    raise ValidationError(_(
                        'Core settings of Walmart are deleted,\
                         please upgrade Walmart Odoo Connector module to back this settings.'))

                name = instance.name + ' : ' + update_stock_cron.name
                vals.update({'name': name})
                new_cron = update_stock_cron.copy(default=vals)
                self.env['ir.model.data'].create(
                    {'module': 'walmart_ept',
                     'name': 'ir_cron_auto_export_inventory_instance_%d' % (
                         instance.id),
                     'model': 'ir.cron',
                     'res_id': new_cron.id,
                     'noupdate': True})

        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_export_inventory_instance_%d' % (instance.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def setup_auto_create_item_report_request(self, instance):
        if self.walmart_auto_create_item_report_request:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_create_item_report_request_%d' % (instance.id))
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.walmart_auto_create_item_report_request_interval_type](
                self.walmart_auto_create_item_report_request_interval_number)
            vals = {'active': True,
                    'interval_number': self.walmart_auto_create_item_report_request_interval_number,
                    'interval_type': self.walmart_auto_create_item_report_request_interval_type,
                    'nextcall': self.walmart_auto_create_item_report_request_next_execution or nextcall.strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'user_id': self.walmart_auto_create_item_report_request_user_id.id,
                    'code': "model.auto_create_item_request_report(instance_id=%d)" % (instance.id)}
            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    get_item_report_cron = self.env.ref('walmart_ept.ir_cron_auto_create_item_report_request')
                except:
                    get_item_report_cron = False
                if not get_item_report_cron:
                    raise ValidationError(_(
                        'Core settings of Walmart are deleted, \
                        please upgrade Walmart Odoo Connector module to back this settings.'))

                name = instance.name + ' : ' + get_item_report_cron.name
                vals.update({'name': name})
                new_cron = get_item_report_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module': 'walmart_ept',
                                                  'name': 'ir_cron_auto_create_item_report_request_%d' % (
                                                      instance.id),
                                                  'model': 'ir.cron',
                                                  'res_id': new_cron.id,
                                                  'noupdate': True})
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_create_item_report_request_%d' % (instance.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def setup_auto_process_item_report(self, instance):
        if self.walmart_auto_process_item_report:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_process_item_report_%d' % (instance.id))
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.walmart_auto_process_item_report_interval_type](
                self.walmart_auto_process_item_report_interval_number)
            vals = {'active': True,
                    'interval_number': self.walmart_auto_process_item_report_interval_number,
                    'interval_type': self.walmart_auto_process_item_report_interval_type,
                    'nextcall': self.walmart_auto_process_item_report_next_execution or nextcall.strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'user_id': self.walmart_auto_process_item_report_user_id.id,
                    'code': "model.auto_process_item_request_report(instance_id=%d)" % (instance.id)}
            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    get_item_report_cron = self.env.ref('walmart_ept.ir_cron_auto_process_item_report')
                except:
                    get_item_report_cron = False
                if not get_item_report_cron:
                    raise ValidationError(_(
                        'Core settings of Walmart are deleted, \
                        please upgrade Walmart Odoo Connector module to back this settings.'))

                name = instance.name + ' : ' + get_item_report_cron.name
                vals.update({'name': name})
                new_cron = get_item_report_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module': 'walmart_ept',
                                                  'name': 'ir_cron_auto_process_item_report_%d' % (
                                                      instance.id),
                                                  'model': 'ir.cron',
                                                  'res_id': new_cron.id,
                                                  'noupdate': True})
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_process_item_report_%d' % (instance.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    # added By sunil sonagra

    def setup_auto_send_invoice_via_email(self, marketplace):
        if self.walmart_auto_send_invoice:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_send_invoice_via_mail_%d' % (marketplace.id))
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.walmart_send_invoice_interval_type](
                self.walmart_send_invoice_interval_number)
            vals = {'active': True,
                    'interval_number': self.walmart_send_invoice_interval_number,
                    'interval_type': self.walmart_send_invoice_interval_type,
                    'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': self.walmart_send_invoice_update_user_id.id,
                    'code': "model.auto_send_invoice_via_cron(instance_id=%d)" % (
                        marketplace.id)}

            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    auto_invoice_cron = self.env.ref(
                        'walmart_ept.ir_cron_auto_send_invoice_via_mail')
                except:
                    auto_invoice_cron = False
                if not auto_invoice_cron:
                    raise ValidationError(_(
                        'Core settings of Walmart are deleted, \
                        please upgrade Walmart Odoo Connector module to back this settings.'))

                name = marketplace.name + ' : ' + auto_invoice_cron.name
                vals.update({'name': name})
                new_cron = auto_invoice_cron.copy(default=vals)
                self.env['ir.model.data'].create(
                    {'module': 'walmart_ept',
                     'name': 'ir_cron_auto_send_invoice_via_mail_%d' % (
                         marketplace.id),
                     'model': 'ir.cron',
                     'res_id': new_cron.id,
                     'noupdate': True})
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_send_invoice_via_mail_%d' % (marketplace.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    # added By sunil sonagra

    def setup_auto_send_refund_invoice_via_email(self, marketplace):
        if self.walmart_auto_send_refund_invoice:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_send_refund_invoice_via_mail_%d' % (marketplace.id))
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.walmart_refund_invoice_send_interval_type](
                self.walmart_refund_invoice_send_interval_number)
            vals = {'active': True,
                    'interval_number': self.walmart_refund_invoice_send_interval_number,
                    'interval_type': self.walmart_refund_invoice_send_interval_type,
                    'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': self.walmart_refund_invoice_send_update_user_id and
                               self.walmart_refund_invoice_send_update_user_id.id,
                    'code': "model.auto_send_refund_invoice_via_cron(instance_id=%d)" % (
                        marketplace.id)}
            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    auto_invoice_cron = self.env.ref(
                        'walmart_ept.ir_cron_auto_send_refund_invoice_via_mail')
                except:
                    auto_invoice_cron = False
                if not auto_invoice_cron:
                    raise ValidationError(_(
                        'Core settings of Walmart are deleted, \
                         please upgrade Walmart Odoo Connector module to back this settings.'))

                name = marketplace.name + ' : ' + auto_invoice_cron.name
                vals.update({'name': name})
                new_cron = auto_invoice_cron.copy(default=vals)
                self.env['ir.model.data'].create(
                    {'module': 'walmart_ept',
                     'name': 'ir_cron_auto_send_refund_invoice_via_mail_%d' % (
                         marketplace.id),
                     'model': 'ir.cron',
                     'res_id': new_cron.id,
                     'noupdate': True})
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_send_refund_invoice_via_mail_%d' % (marketplace.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def setup_walmart_import_order_cron(self, instance):
        """
        Cron for auto Import Orders
        :param instance:
        :return:
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 11/01/2022.
        """
        try:
            cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_import_walmart_orders_instance_%d' % instance.id)
        except:
            cron_exist = False

        if self.auto_import_walmart_orders:
            nextcall = datetime.now() + _intervalTypes[self.auto_import_walmart_orders_interval_type](
                self.auto_import_walmart_orders_interval_number)
            vals = {'active': True,
                    'interval_number': self.auto_import_walmart_orders_interval_number,
                    'interval_type': self.auto_import_walmart_orders_interval_type,
                    'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': self.auto_import_walmart_orders_user_id.id,
                    'code': "model.import_order_cron_action(ctx={'walmart_instance_id':%d})" % instance.id}
            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    core_cron = self.env.ref(
                        'walmart_ept.ir_cron_auto_import_walmart_orders')
                except:
                    core_cron = False
                if not core_cron:
                    raise ValidationError(_(
                        'Core settings of Walmart are deleted, \
                        please upgrade Walmart Odoo Connector module to back this settings.'))

                name = instance.name + ' : ' + core_cron.name
                vals.update({'name': name})
                new_cron = core_cron.copy(default=vals)
                self.env['ir.model.data'].create(
                    {'module': 'walmart_ept',
                     'name': 'ir_cron_auto_import_walmart_orders_instance_%d' % (instance.id),
                     'model': 'ir.cron',
                     'res_id': new_cron.id,
                     'noupdate': True})
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_import_walmart_orders_instance_%d' % (instance.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def setup_walmart_import_wfs_order_cron(self, instance):
        """
        Cron for auto Import Walmart WFS Orders
        :param instance:
        :return:
        @author: Yagnik Joshi @Emipro Technologies Pvt. Ltd on date 05/10/2022.
        """
        try:
            cron_exist = self.env.ref('walmart_ept.ir_cron_auto_import_walmart_wfs_orders_instance_%d' % instance.id)
        except:
            cron_exist = False

        if self.auto_import_walmart_wfs_orders:
            nextcall = datetime.now() + _intervalTypes[self.auto_import_walmart_wfs_orders_interval_type](
                self.auto_import_walmart_wfs_orders_interval_number)
            vals = {
                'active': True,
                'interval_number': self.auto_import_walmart_wfs_orders_interval_number,
                'interval_type': self.auto_import_walmart_wfs_orders_interval_type,
                'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.auto_import_walmart_wfs_orders_user_id.id,
                'code': "model.import_wfs_order_cron_action(ctx={'walmart_instance_id':%d})" % instance.id
            }
            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    core_cron = self.env.ref('walmart_ept.ir_cron_auto_import_walmart_wfs_orders')
                except:
                    core_cron = False
                if not core_cron:
                    raise ValidationError(
                        _('Core Settings of Walmart are deleted, \ Please upgrade Walmart Odoo Connector module to back this settings.'))

                name = instance.name + ' : ' + core_cron.name
                vals.update({'name': name})
                new_cron = core_cron.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module': 'walmart_ept',
                    'name': 'ir_cron_auto_import_walmart_wfs_orders_instance_%d' % (instance.id),
                    'model': 'ir.cron',
                    'res_id': new_cron.id,
                    'noupdate': True
                })
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_import_walmart_wfs_orders_instance_%d' % (instance.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def setup_walmart_import_wfs_inventory_cron(self, instance):
        """
        Cron for auto Import Walmart WFS Inventory
        :param instance:
        :return:
        @author: Yagnik Joshi @Emipro Technologies Pvt. Ltd on date 19/12/2022.
        """
        try:
            cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_import_walmart_wfs_inventory_instance_%d' % (instance.id))
        except:
            cron_exist = False

        if self.auto_import_walmart_wfs_inventory:
            nextcall = datetime.now() + _intervalTypes[self.auto_import_walmart_wfs_inventory_interval_type](
                self.auto_import_walmart_wfs_inventory_interval_number)
            vals = {
                'active': True,
                'interval_number': self.auto_import_walmart_wfs_inventory_interval_number,
                'interval_type': self.auto_import_walmart_wfs_inventory_interval_type,
                'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.auto_import_walmart_wfs_inventory_user_id.id,
                'code': "model.auto_import_walmart_wfs_inventory_via_cron(ctx={'walmart_instance_id':%d})" % instance.id
            }
            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    core_cron = self.env.ref('walmart_ept.ir_cron_auto_import_walmart_wfs_inventory')
                except:
                    core_cron = False
                if not core_cron:
                    raise ValidationError(
                        _('Core Settings of Walmart are deleted, \ Please upgrade Walmart Odoo Connector module to back this settings.'))

                name = instance.name + ' : ' + core_cron.name
                vals.update({'name': name})
                new_cron = core_cron.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module': 'walmart_ept',
                    'name': 'ir_cron_auto_import_walmart_wfs_inventory_instance_%d' % (instance.id),
                    'model': 'ir.cron',
                    'res_id': new_cron.id,
                    'noupdate': True
                })
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_import_walmart_wfs_inventory_instance_%d' % (instance.id))
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True

    def setup_walmart_import_reconciliation_report_cron(self, instance):
        """
        Define this method for setup import and process walmart reconciliation report scheduler.
        :param instance: walmart.marketplace.ept()
        :return: True
        """
        try:
            cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_import_walmart_reconciliation_report_instance_%d' % (instance.id),
                raise_if_not_found=False)
        except:
            cron_exist = False
        if self.auto_import_walmart_reconciliation_report:
            nextcall = datetime.now() + _intervalTypes[self.auto_import_walmart_reconciliation_report_interval_type](
                self.auto_import_walmart_reconciliation_report_interval_number)
            vals = {
                'active': True,
                'interval_number': self.auto_import_walmart_reconciliation_report_interval_number,
                'interval_type': self.auto_import_walmart_reconciliation_report_interval_type,
                'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.auto_import_walmart_reconciliation_report_user_id.id,
                'code': "model.auto_import_walmart_reconciliation_report_ept(ctx={'walmart_instance_id':%d})" % instance.id
            }
            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    core_cron = self.env.ref('walmart_ept.ir_cron_auto_import_walmart_reconciliation_report',
                                             raise_if_not_found=False)
                except:
                    core_cron = False
                if not core_cron:
                    raise ValidationError(
                        _('Core Settings of Walmart are deleted, \ Please upgrade Walmart Odoo Connector module to back this settings.'))

                name = instance.name + ' : ' + core_cron.name
                vals.update({'name': name})
                new_cron = core_cron.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module': 'walmart_ept',
                    'name': 'ir_cron_auto_import_walmart_reconciliation_report_instance_%d' % (instance.id),
                    'model': 'ir.cron',
                    'res_id': new_cron.id,
                    'noupdate': True
                })
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_import_walmart_reconciliation_report_instance_%d' % (instance.id),
                    raise_if_not_found=False)
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        self.setup_walmart_process_reconciliation_report_cron(instance)
        return True

    def setup_walmart_process_reconciliation_report_cron(self, instance):
        """
        Define this method for setup auto process reconciliation report scheduler.
        :param instance: walmart.marketplace.ept()
        :return: True
        """
        try:
            cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_process_walmart_reconciliation_report_instance_%d' % (instance.id),
                raise_if_not_found=False)
        except:
            cron_exist = False
        if self.auto_import_walmart_reconciliation_report:
            nextcall = (datetime.now() + _intervalTypes[self.auto_import_walmart_reconciliation_report_interval_type](
                self.auto_import_walmart_reconciliation_report_interval_number)) + relativedelta(minutes=10)
            vals = {
                'active': True,
                'interval_number': self.auto_import_walmart_reconciliation_report_interval_number,
                'interval_type': self.auto_import_walmart_reconciliation_report_interval_type,
                'nextcall': nextcall,
                'user_id': self.auto_import_walmart_reconciliation_report_user_id.id,
                'code': "model.auto_process_walmart_reconciliation_report_ept(ctx={'walmart_instance_id':%d})" % instance.id
            }
            if cron_exist:
                vals.update({'name': cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    core_cron = self.env.ref('walmart_ept.ir_cron_auto_process_walmart_reconciliation_report',
                                             raise_if_not_found=False)
                except:
                    core_cron = False
                if not core_cron:
                    raise ValidationError(
                        _('Core Settings of Walmart are deleted, \ Please upgrade Walmart Odoo Connector module to back this settings.'))

                name = instance.name + ' : ' + core_cron.name
                vals.update({'name': name})
                new_cron = core_cron.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module': 'walmart_ept',
                    'name': 'ir_cron_auto_process_walmart_reconciliation_report_instance_%d' % (instance.id),
                    'model': 'ir.cron',
                    'res_id': new_cron.id,
                    'noupdate': True
                })
        else:
            try:
                cron_exist = self.env.ref(
                    'walmart_ept.ir_cron_auto_process_walmart_reconciliation_report_instance_%d' % (instance.id),
                    raise_if_not_found=False)
            except:
                cron_exist = False
            if cron_exist:
                cron_exist.write({'active': False})
        return True
