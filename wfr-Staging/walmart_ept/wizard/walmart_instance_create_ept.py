from odoo import fields, models, _, api
from odoo.exceptions import ValidationError, UserError
from ..walmart_api.walmart_call_api import Walmart


class WalmartInstanceCreate(models.TransientModel):
    _name = 'walmart.instance.create.ept'
    _description = 'Configuration for Creating Walmart Instance'

    name = fields.Char(string="Walmart Name", help="Walmart Name")
    walmart_consumer_id = fields.Char(string="Consumer", help="Consumer Name")
    walmart_secret_key = fields.Text(string="Walmart Secret Key", help="Secret Key")
    walmart_country_id = fields.Many2one('res.country', string="Country", help="Country")
    walmart_channel_type = fields.Char(string="Channel",
                                       default='0f3e4dd4-0514-4346-b39d-af0e00ea066d',
                                       help="Channel Type")
    environment = fields.Selection([('sandbox', 'Sandbox'), ('production', 'Production')])
    is_selling_on_wfs = fields.Boolean("Are you selling on WFS? ", default=False,
                                    help="If it's checked, WFS Order will be Imported.")

    # update_notification = fields.Boolean(string="Get Update Notification?",
    #                                      help="If Enable, then You will be notify for the latest version app.")
    # customer_so_number = fields.Char("App Order Number", help="Your App Purchase Registered Number")

    """This method is used to create new walmart marketplace,
    if walmart marketplace of the provided credentials does not
    exists.
        @param None.
        @return: Res
        @author: Harshit Trivedi on dated 01-MAR-2019
    """

    def test_walmart_connection(self):
        walmart_marketplace_obj = self.env['walmart.marketplace.ept']
        product_pricelist_obj = self.env['product.pricelist']
        marketplace_exist = self.env['walmart.marketplace.ept'].search(
            [('consumer_id', '=', self.walmart_consumer_id),
             ('walmart_channel_type', '=', self.walmart_channel_type),
             ('walmart_secret_key', '=', self.walmart_secret_key)])
        if marketplace_exist:
            raise ValidationError(_('Marketplace already exist with given Credential.'))
        try:
            conn_obj = Walmart(client_id=self.walmart_consumer_id, client_secret=self.walmart_secret_key,
                               environment=self.environment, country_code=self.walmart_country_id.code.lower())
        except Exception as error:
            raise UserError(error)
        if conn_obj:
            lang_id = self.env['res.lang'].search([('code', '=', 'en_US')])

            currency_id = self.walmart_country_id.currency_id.id
            company_id = self.env.user.company_id.id
            price_list_name = self.name + " " + "PriceList"
            price_list = product_pricelist_obj.search(
                [('name', '=', price_list_name), ('currency_id', '=', currency_id), ('company_id', '=', company_id)],
                limit=1)
            if not price_list:
                pricelist_vals = {'name': self.name + " Pricelist",
                                  'discount_policy': 'with_discount',
                                  'company_id': company_id, 'currency_id': currency_id}
                price_list = product_pricelist_obj.create(pricelist_vals)

            sales_team = self.create_sales_channel(self.name)

            settlement_journal_id = self.get_journal(price_list)

            marketplace_vals = {'name': self.name, 'consumer_id': self.walmart_consumer_id,
                                'walmart_secret_key': self.walmart_secret_key,
                                'country_id': self.walmart_country_id.id,
                                'is_selling_on_wfs': self.is_selling_on_wfs,
                                'walmart_channel_type': self.walmart_channel_type,
                                'lang_id': lang_id.id or False,
                                'pricelist_id': price_list.id,
                                'team_id': sales_team.id,
                                'settlement_report_journal_id': settlement_journal_id,
                                'environment': self.environment}

            marketplace_id = walmart_marketplace_obj.create(marketplace_vals)

            # if marketplace_id and self.update_notification:
            #     config_setting = self.env['res.config.settings']
            #     config_setting.update_system_param(self.update_notification, self.customer_so_number)
            #     config_setting.enable_emipro_notification(self.update_notification)

            if self._context.get('is_calling_from_onboarding_panel', False):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            action = self.env.ref('walmart_ept.action_walmart_configuration', False)
            res = action and action.read()[0] or {}
            res['context'] = {'default_walmart_marketplace_id': marketplace_id.id,
                              'module': 'walmart_ept'}
            return res

    # @api.model
    # def default_get(self, fields):
    #     res = super(WalmartInstanceCreate, self).default_get(fields)
    #     is_notify, customer_so_number = self.env['res.config.settings'].get_in_app_system_parameter()
    #     res['update_notification'] = is_notify
    #     res['customer_so_number'] = customer_so_number
    #     return res

    def create_sales_channel(self, name):
        """
        It creates new sales team for Walmart instance.
        :param name: Name of sale channel and it always the name of the instance.
        """
        crm_team_obj = self.env['crm.team']
        vals = {
            'name': name,
            'use_quotations': True
        }
        return crm_team_obj.create(vals)

    def get_journal(self, price_list):
        """
        create or set settlement report journal
        :return: True
        """
        account_journal_obj = self.env['account.journal']

        code = "%s%s" % ('Wal', self.walmart_country_id.code)
        journal_id = account_journal_obj.search([('code', '=', code),
                                                 ('company_id', '=', self.env.user.company_id.id)])
        if not journal_id:
            journal_values = self.prepare_journal_vals(price_list, code)
            journal_id = account_journal_obj.create(journal_values)

            if not journal_id.currency_id.active:
                journal_id.currency_id.active = True

        return journal_id.id

    def prepare_journal_vals(self, pricelist, code):
        journal_values = {
            'name': self.name,
            'type': 'bank',
            'code': code,
            'currency_id': pricelist.currency_id.id,
            'company_id': self.env.user.company_id.id
        }
        return journal_values
