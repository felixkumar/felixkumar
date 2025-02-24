import os
import zipfile

from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

from odoo import fields, models, api, _, SUPERUSER_ID

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7 * interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}

class WalmartConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Configuration for Walmart'

    walmart_marketplace_id = fields.Many2one('walmart.marketplace.ept',
                                             string="Walmart Marketplace",
                                             help="Select Walmart Marketplace")
    walmart_consumer_id = fields.Char(string="Consumer", help="Consumer Name")
    walmart_secret_key = fields.Text(string="Walmart Secret Key", help="Secret Key")
    walmart_country_id = fields.Many2one('res.country', string="Country", help="Country")
    walmart_country_code = fields.Char(related='walmart_country_id.code', string="Walmart Country code")
    walmart_channel_type = fields.Char(string="Channel",
                                       default='0f3e4dd4-0514-4346-b39d-af0e00ea066d',
                                       help="Channel Type")
    walmart_warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", help="Warehouse")
    walmart_wfs_warehouse_id = fields.Many2one('stock.warehouse', string="WFS Warehouse", help="WFS Warehouse")
    is_selling_on_wfs = fields.Boolean("Are you selling on WFS? ", default=False,
                                       help="If it's checked, WFS Order will be Imported.")
    walmart_pricelist_id = fields.Many2one('product.pricelist', string="PriceList",
                                           help="Product PriceList")
    walmart_lang_id = fields.Many2one('res.lang', string="Language", help="Language")
    walmart_auto_workflow_id = fields.Many2one('sale.workflow.process.ept', string='Auto Workflow',
                                               help="Auto Invoice Workflow")
    walmart_shipping_product_id = fields.Many2one("product.product", "Shipping Product",
                                                  domain=[('type', '=', 'service')])
    walmart_discount_product_id = fields.Many2one("product.product", "Discount Product",
                                                  domain=[('type', '=', 'service')])
    walmart_auto_create_product_not_found_in_odoo = fields.Boolean(
            'Auto Create Offer Not Found in Odoo',
            help="If it is ticked it will automatically \
        create offer[product] in odoo as well as in walmart")
    walmart_is_default_odoo_sequence_in_sales_order = fields.Boolean(
            'Is Default Odoo Sequence In Sale Order', default=True)
    walmart_order_prefix = fields.Char(size=10, string='Order Prefix')
    walmart_company_id = fields.Many2one('res.company', string="Walmart Company",
                                         help="Company of the User")
    walmart_payment_term_id = fields.Many2one('account.payment.term', string='Payment Term',
                                              help="Payment Term for Doing Payment")
    is_walmart_import_shipped_orders = fields.Boolean('Is Import Shipped Orders',
                                                      help="Walamrt Orders are Shipped Order not ")
    walmart_ship_start_date = fields.Datetime(string="ShipOrder Start Date")

    # Added By Harshit Trivedi
    walmart_stock_field_id = fields.Many2one('ir.model.fields', string='Inventory Field')

    # Added By Harshit Trivedi
    walmart_auto_create_refund = fields.Boolean("Auto Create Refund ?", default=True)
    # Added by sunil songra
    walmart_team_id = fields.Many2one('crm.team', string='Sales Team')
    walmart_settlement_report_journal_id = fields.Many2one('account.journal',
                                                           string='Settlement Report Journal')

    walmart_tax_id = fields.Many2one('account.tax', string='Default Sales Tax')


    @api.onchange('walmart_marketplace_id')
    def onchange_walmart_marketplace_id(self):
        vals = {}
        if self.walmart_marketplace_id:
            marketplace_id = self.walmart_marketplace_id
            vals['walmart_consumer_id'] = marketplace_id.consumer_id or False
            vals['walmart_secret_key'] = marketplace_id.walmart_secret_key or False
            vals[
                'walmart_country_id'] = marketplace_id.country_id.id
            vals['walmart_channel_type'] = marketplace_id.walmart_channel_type or False
            vals[
                'walmart_warehouse_id'] = marketplace_id.warehouse_id.id
            vals[
                'walmart_wfs_warehouse_id'] = marketplace_id.wfs_warehouse_id.id
            vals['is_selling_on_wfs'] =  \
                marketplace_id.is_selling_on_wfs or False
            vals[
                'walmart_pricelist_id'] = marketplace_id.pricelist_id.id
            vals['walmart_lang_id'] = marketplace_id.lang_id.id
            vals[
                'walmart_shipping_product_id'] = marketplace_id.shipping_product_id.id
            vals[
                'walmart_discount_product_id'] = marketplace_id.discount_product_id.id
            vals[
                'walmart_auto_workflow_id'] = marketplace_id.walmart_auto_workflow_id.id
            vals['walmart_auto_create_product_not_found_in_odoo'] = \
                marketplace_id.auto_create_product_not_found_in_odoo or False
            vals['walmart_is_default_odoo_sequence_in_sales_order'] \
                = marketplace_id.is_default_odoo_sequence_in_sales_order or False
            vals['walmart_order_prefix'] = marketplace_id.order_prefix or False
            vals['walmart_company_id'] = marketplace_id.company_id.id
            vals['walmart_payment_term_id'] = marketplace_id.payment_term_id.id
            vals['is_walmart_import_shipped_orders'] = marketplace_id.is_import_shipped_orders
            vals['walmart_ship_start_date'] = marketplace_id.ship_order_start_date or False
            vals['walmart_auto_create_refund'] = marketplace_id.auto_create_refund or False
            vals['walmart_stock_field_id'] = marketplace_id.stock_field_id.id
            vals['walmart_team_id'] = marketplace_id.team_id or False
            vals['walmart_settlement_report_journal_id'] = \
                marketplace_id.settlement_report_journal_id or False
            vals['walmart_tax_id'] = marketplace_id.walmart_tax_id.id or False

        return {'value': vals}

    def execute(self):
        marketplace_id = self.walmart_marketplace_id
        values = {}
        res = super(WalmartConfigSettings, self).execute()
        ctx = {}
        if marketplace_id:

            country_currency = self.walmart_country_id.currency_id.id
            pricelist_currency = self.walmart_pricelist_id.currency_id.id

            if country_currency != pricelist_currency:
                raise ValidationError(_('\
                Country Currency and Pricelist Currency does not matched..!'))

            ctx.update({'default_marketplace_id': marketplace_id.id})

            values['country_id'] = self.walmart_country_id.id
            values['warehouse_id'] = self.walmart_warehouse_id.id
            values['wfs_warehouse_id'] = self.walmart_wfs_warehouse_id.id
            values['is_selling_on_wfs'] = \
                self.is_selling_on_wfs or False
            values['pricelist_id'] = self.walmart_pricelist_id.id
            values['lang_id'] = self.walmart_lang_id.id
            values['shipping_product_id'] = self.walmart_shipping_product_id.id
            values['discount_product_id'] = self.walmart_discount_product_id.id
            values['walmart_auto_workflow_id'] = self.walmart_auto_workflow_id.id
            values['auto_create_product_not_found_in_odoo'] = \
                self.walmart_auto_create_product_not_found_in_odoo or False
            values['is_default_odoo_sequence_in_sales_order'] = \
                self.walmart_is_default_odoo_sequence_in_sales_order or False
            values['order_prefix'] = self.walmart_order_prefix or False
            values['company_id'] = self.walmart_company_id.id
            values['payment_term_id'] = self.walmart_payment_term_id.id
            values['is_import_shipped_orders'] = self.is_walmart_import_shipped_orders or False
            values['ship_order_start_date'] = self.walmart_ship_start_date or False
            values['auto_create_refund'] = self.walmart_auto_create_refund or False
            values['stock_field_id'] = self.walmart_stock_field_id.id
            values['team_id'] = self.walmart_team_id.id
            values['settlement_report_journal_id'] = self.walmart_settlement_report_journal_id.id
            values['walmart_tax_id'] = self.walmart_tax_id.id or False

            marketplace_id.write(values)
        return res

    def install_tax_calculate_module(self):
        path = os.path.realpath(
                os.path.join(os.path.dirname(__file__), '../data/account_tax_python_ept.zip'))
        extract_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '../../'))
        if not os.path.exists(extract_path + '/account_tax_python_ept'):
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        self.env['ir.module.module'].update_list()
        module = self.env['ir.module.module'].search([
            ('name', '=', 'account_tax_python_ept'),
            ('state', '=', 'uninstalled')
        ])
        if module:
            module.with_user(SUPERUSER_ID).button_immediate_install()
        action = self.env.ref('walmart_ept.action_walmart_configuration', False)
        res = action and action.read()[0] or {}
        res['context'] = {'default_walmart_marketplace_id': self.walmart_marketplace_id.id,
                          'module': 'walmart_ept'}
        return res

    # Below method are use for the onboarding panel

    @api.model
    def action_open_walmart_instance_wizard(self):
        """ This action is used to set default value in the instance wizard of on boarding panel.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 23 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        action = self.env["ir.actions.actions"]._for_xml_id(
                "walmart_ept.walmart_on_board_instance_configuration_action")
        action['context'] = {'is_calling_from_onboarding_panel': True}
        instance = self.env['walmart.marketplace.ept'].search_walmart_marketplace()
        if instance:
            action.get('context').update({
                'default_name': instance.name,
                'default_walmart_consumer_id': instance.consumer_id,
                'default_walmart_country_id': instance.country_id.id,
                'default_environment': instance.environment,
                'default_walmart_secret_key': instance.walmart_secret_key,
                'default_is_selling_on_wfs': instance.is_selling_on_wfs,
                'is_already_instance_created': True,
            })
            company = instance.company_id
            if company.walmart_instance_onboarding_state != 'done':
                company.set_onboarding_step_done('walmart_instance_onboarding_state')
        return action

    @api.model
    def action_walmart_open_general_configuration_wizard(self):
        """ Prepare the action for open the general configurations wizard.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 23 July 2021 .
            Task_id: 175221 - BOl.com panel
        """
        try:
            view_id = self.env.ref('walmart_ept.walmart_general_configurations_onboarding_wizard_view')
        except:
            return True
        return self.walmart_general_config_view_action(view_id)

    @api.model
    def action_walmart_open_cron_configuration_wizard(self):
        """ Prepare the action for open the cron configurations wizard.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 23 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        try:
            view_id = self.env.ref('walmart_ept.walmart_onboarding_cron_configuration_ept_form_view')
        except:
            return True
        return self.walmart_cron_config_view_action(view_id)

    def walmart_general_config_view_action(self, view_id):
        """ Return the action for general configurations wizard.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 23 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        action = self.env["ir.actions.actions"]._for_xml_id(
                "walmart_ept.action_walmart_general_config")
        action_data = {'view_id': view_id.id, 'views': [(view_id.id, 'form')], 'target': 'new',
                       'name': 'Configurations'}
        instance = self.env['walmart.marketplace.ept'].search_walmart_marketplace()
        if instance:
            action['context'] = {'default_walmart_marketplace_id': instance.id}
        else:
            action['context'] = {}
        action.update(action_data)
        return action

    def walmart_save_general_configurations(self):
        """ This method is used to set the general configuration of Walmart from the Panel.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 26 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        instance = self.walmart_marketplace_id
        if instance:
            configuration_vals = self.prepare_vals_for_general_configuration()
            instance.write(configuration_vals)
            company = instance.company_id
            company.set_onboarding_step_done('walmart_general_configuration_onboarding_state')

    def prepare_vals_for_general_configuration(self):
        """ This method is use to prepare a vals for the general configuration.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 21 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        vals = {}
        vals.update({'country_id': self.walmart_country_id.id,
                     'pricelist_id': self.walmart_pricelist_id.id,
                     'warehouse_id': self.walmart_warehouse_id.id,
                     'wfs_warehouse_id': self.walmart_wfs_warehouse_id.id,
                     'is_selling_on_wfs': self.is_selling_on_wfs,
                     'lang_id': self.walmart_lang_id.id,
                     'company_id': self.walmart_company_id.id,
                     'payment_term_id': self.walmart_payment_term_id.id,
                     'team_id': self.walmart_team_id.id,
                     'settlement_report_journal_id': self.walmart_settlement_report_journal_id.id,
                     'auto_create_product_not_found_in_odoo': self.walmart_auto_create_product_not_found_in_odoo,
                     'shipping_product_id': self.walmart_shipping_product_id.id,
                     'discount_product_id': self.walmart_discount_product_id.id,
                     'walmart_auto_workflow_id': self.walmart_auto_workflow_id.id,
                     'is_default_odoo_sequence_in_sales_order': self.walmart_is_default_odoo_sequence_in_sales_order,
                     'order_prefix': self.walmart_order_prefix,
                     'stock_field_id': self.walmart_stock_field_id
                     })
        return vals

    def walmart_cron_config_view_action(self, view_id):
        """ Return the action for cron configurations wizard.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 23 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        action = self.env["ir.actions.actions"]._for_xml_id(
                "walmart_ept.action_wizard_onboarding_walmart_cron_configuration_ept")
        action_data = {'view_id': view_id.id, 'views': [(view_id.id, 'form')], 'target': 'new',
                       'name': 'Configurations'}
        instance = self.env['walmart.marketplace.ept'].search_walmart_marketplace()
        if instance:
            action['context'] = {'default_walmart_marketplace_id': instance.id,
                                 'is_instance_exists': True}
        else:
            action['context'] = {}
        action['context'].update({'is_calling_from_onboarding_panel': True})
        action.update(action_data)
        return action
