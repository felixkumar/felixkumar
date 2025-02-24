# -*- coding: utf-8 -*-
# Copyright 2023 IZI PT Solusi Usaha Mudah

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_marketplace_selection = [
    ('tokopedia', 'Tokopedia'),
    ('shopee', 'Shopee'),
    ('lazada', 'Lazada'),
    ('tiktok', 'TikTok Shop'),
]


class MarketplaceAccount(models.Model):
    _name = 'mp.account'
    _description = 'Marketplace Account'

    # @api.multi
    @api.constrains()
    def _check_required_if_marketplace(self):
        """ If the field has 'required_if_marketplace="<marketplace>"' attribute, then it
        required if record.marketplace is <marketplace>. """
        empty_field = []
        for record in self:
            for k, f in record._fields.items():
                if getattr(f, 'required_if_marketplace', None) == record.marketplace and not record[k]:
                    empty_field.append('Field %(field)s at ID %(id)s is empty.' % {
                        'field': self.env['ir.model.fields'].search([
                            ('name', '=', k),
                            ('model', '=', record._name)
                        ]).field_description,
                        'id': record.id,
                    })
        if empty_field:
            raise ValidationError(', '.join(empty_field))
        return True

#     _constraints = [
#         (_check_required_if_marketplace, 'Required fields not filled', []),
#     ]

    MP_ACCOUNT_STATES = [
        ('new', 'New'),
        ('authenticating', 'Authenticating'),
        ('authenticated', 'Authenticated'),
    ]

    READONLY_STATES = {
        'authenticated': [('readonly', True)],
        'authenticating': [('readonly', True)],
    }

    _AWB_ACTION_TYPE = [
        ('open', 'Open AWB in new Tab'),
        ('download', 'Auto Downloadable AWB'),
        ('print', 'Direct Print AWB')
    ]

    name = fields.Char(string="Name", required=True)
    marketplace = fields.Selection(string="Marketplace", selection=_marketplace_selection,
                                   required=True, states=READONLY_STATES)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company", index=1, readonly=False, required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(),
                                 states=READONLY_STATES)
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=True,
                                  default=lambda s: s.env.ref('base.IDR'))
    state = fields.Selection(string="Status", selection=MP_ACCOUNT_STATES, required=True, default="new",
                             states=READONLY_STATES)
    mp_token_ids = fields.One2many(comodel_name="mp.token", inverse_name="mp_account_id", string="Marketplace Tokens",
                                   required=False, states=READONLY_STATES)
    mp_token_id = fields.Many2one(comodel_name="mp.token", string="Marketplace Token", compute="_compute_mp_token")
    access_token = fields.Char(string="Access Token", related="mp_token_id.name", readonly=True)
    access_token_expired_date = fields.Datetime(string="Expired Date", related="mp_token_id.expired_date",
                                                readonly=True)
    auth_message = fields.Char(string="Authentication Message", readonly=True)
    mp_product_ids = fields.One2many(comodel_name="mp.product", inverse_name="mp_account_id",
                                     string="Marketplace Product(s)")
    warehouse_id = fields.Many2one('stock.warehouse', string='Default Warehouse Marketplace')
    insurance_product_id = fields.Many2one(comodel_name="product.product", string="Default Insurance Product",
                                           default=lambda self: self._get_default_insurance_product_id())
    partner_id = fields.Many2one(comodel_name='res.partner', string='Default Customer')
    team_id = fields.Many2one(comodel_name='crm.team', string='Default Sales Team')
    user_id = fields.Many2one(comodel_name='res.users', string='Default Salesperson')
    payment_term_id = fields.Many2one('account.payment.term', string='Default Payment Terms')
    pricelist_id = fields.Many2one('product.pricelist', string='Default Pricelist')

    global_discount_product_id = fields.Many2one(comodel_name="product.product",
                                                 string="Default Global Discount Product",
                                                 default=lambda self: self._get_default_global_discount_product_id())
    adjustment_product_id = fields.Many2one(comodel_name="product.product",
                                            string="Default Adjustment Product",
                                            default=lambda self: self._get_default_adjustment_product_id())
    create_invoice = fields.Boolean(string="Auto Create Invoice", default=False,
                                    help="Auto creating invoices after confirm sale order")
    auto_confirm = fields.Boolean(string="Auto Confirm Sale Order", default=False,
                                  help="Auto Confirm Sale Order if order status has processed")
    create_invoice_after_delivery = fields.Boolean(string="Auto Create Invoice After Delivery", default=False,
                                    help="Auto creating invoices after validate delivery order") 
    keep_order_date = fields.Boolean(string="Keep Order Date", default=True,
                                     help="Keep Order date when Confirm Sales Order")
    get_unpaid_orders = fields.Boolean(string="Get Unpaid Order", default=False,
                                       help="Get order with status UNPAID from Shopee")
    get_cancelled_orders = fields.Boolean(string="Get Cancelled Order", default=False,
                                          help="Get order CANCELLED from marketplace if the order is not exists before")
    auto_print_label = fields.Boolean(string="Auto Print Shipping Label", default=False,
                                      help="Auto Print Shipping Label after Validating Stock Transfer")
    default_awb_action = fields.Selection(selection=_AWB_ACTION_TYPE, string='AWB Action Type', default='open')
    auto_process_orders = fields.Boolean(
        string="Auto Ship MP Order", help='If you are activate this feature, the system will be automatic processing order to marketplace')
    debug_force_update = fields.Boolean(string="Force Update", default=False,
                                        help="Force update even there is no changes from marketplace")
    debug_force_update_raw = fields.Boolean(string="Force Update Raw Only", default=False,
                                            help="Force update raw field only")
    debug_store_product_img = fields.Boolean(string="Store Product Image",
                                             default=False, help="Store product image as binary into the database")
    debug_product_limit = fields.Integer(string="Product Import Limit", required=True, default=0,
                                         help="Maximum number to import product, set 0 for unlimited!")
    debug_order_limit = fields.Integer(string="Order Import Limit", required=True, default=0,
                                       help="Maximum number to import order, set 0 for unlimited!")
    debug_skip_error = fields.Boolean(string="Skip Error", default=False,
                                      help="Skip error when processing records from marketplace")

    cron_id = fields.Many2one(comodel_name='ir.cron', string='Order Scheduler')
    cron_user_id = fields.Many2one('res.users', string='Scheduler User', related='cron_id.user_id')
    cron_interval_number = fields.Integer(string="Sync Every", default=1,
                                          help="Repeat every x.", related='cron_id.interval_number')
    cron_nextcall = fields.Datetime(string='Next Execution Date', related='cron_id.nextcall')
    cron_interval_type = fields.Selection(string='Interval Unit',
                                          default='minutes', related='cron_id.interval_type')
    cron_active = fields.Boolean(string='Active Scheduler', related='cron_id.active', readonly=False)
    cron_ids = fields.One2many(comodel_name='ir.cron', inverse_name='mp_account_id',
                               string='Scheduled Actions', domain=['|', ('active', '=', True), ('active', '=', False)],
                               context={'active_test': False})
    mp_log_error_ids = fields.One2many(comodel_name='mp.log.error',
                                       inverse_name='mp_account_id', string='Marketplace Log Error')
    partner_id_as_partner_invoice = fields.Boolean(string='Default Customer as Customer Invoice?', default=False)
    default_mp_product = fields.Many2one(comodel_name='mp.product', string='Marketplace Product Template')
    mp_map_product_ids = fields.One2many(comodel_name="mp.map.product", inverse_name="mp_account_id",
                                         string="Marketplace Map Product")

    @api.model
    def create(self, vals):
        res = super(MarketplaceAccount, self).create(vals)
        if not res.cron_id:
            order_cron = self.env['ir.cron'].sudo().create({
                'name': 'IZI %s Order Scheduler %s' % (str(res.marketplace.capitalize()), str(res.id)),
                'model_id': self.env.ref('%s.model_%s' % (self._module, '_'.join(self._name.split('.')))).id,
                'state': 'code',
                'code': "model.%s_get_orders(id=%d,time_range='last_hour',params='by_date_range');" %
                ((res.marketplace), (res.id)),
                'interval_number': 5,
                'interval_type': 'minutes',
                'numbercall': -1,
                'active': False,
                'mp_account_id': res.id
            })
            auto_ship_order = self.env['ir.cron'].sudo().create({
                'name': 'IZI %s Auto Ship Order %s' % (str(res.marketplace.capitalize()), str(res.id)),
                'model_id': self.env.ref('%s.model_%s' % (self._module, '_'.join(self._name.split('.')))).id,
                'state': 'code',
                'code': "model.auto_ship_orders(id=%d, tz=timezone('%s'));" % ((res.id), self._context.get('tz', 'Asia/Jakarta')),
                'interval_number': 2,
                'interval_type': 'minutes',
                'numbercall': -1,
                'active': False,
                'mp_account_id': res.id
            })
            product_cron = self.env['ir.cron'].sudo().create({
                'name': 'IZI %s Product Scheduler %s' % (str(res.marketplace.capitalize()), str(res.id)),
                'model_id': self.env.ref('%s.model_%s' % (self._module, '_'.join(self._name.split('.')))).id,
                'state': 'code',
                'code': "model.%s_get_products(id=%d);" %
                ((res.marketplace), (res.id)),
                'interval_number': 10,
                'interval_type': 'minutes',
                'numbercall': -1,
                'active': False,
                'mp_account_id': res.id
            })
            res.cron_id = order_cron.id
        return res

    @api.constrains('marketplace')
    def check_marketplace_installed(self):
        for rec in self:
            module_name = 'izi_%s' % (rec.marketplace)
            check_module_install = self.env['ir.module.module'].sudo().search([
                ('name', '=', module_name),
                ('state', '=', 'installed'),
            ], count=True)
            if not check_module_install:
                raise ValidationError('Module %s not installed.' % (module_name))

    @api.constrains('name')
    def check_marketplace_name(self):
        for rec in self:
            if not rec.team_id:
                rec.team_id = self.env['crm.team'].create({'name': rec.name})

    @api.onchange('create_invoice')
    def onchange_create_invoice(self):
        if self.create_invoice:
            return {'warning': {'title': 'Warning Message',
                                'message': 'If you enable this feauture will be set product in order lines to ordered quantity'}}

    # @api.multi
    def _compute_mp_token(self):
        for mp_account in self:
            if mp_account.mp_token_ids:
                mp_token = mp_account.mp_token_ids.sorted('expired_date', reverse=True)[0]
                mp_token = mp_token.validate_current_token()
                mp_account.mp_token_id = mp_token.id
            else:
                mp_account.mp_token_id = False

    @api.model
    def _get_default_insurance_product_id(self):
        mp_insurance_product_tmpl = self.env.ref('izi_marketplace.product_tmpl_mp_insurance', raise_if_not_found=False)
        if mp_insurance_product_tmpl:
            return mp_insurance_product_tmpl.product_variant_id.id
        return False

    @api.model
    def _get_default_global_discount_product_id(self):
        mp_global_discount_product_tmpl = self.env.ref('izi_marketplace.product_tmpl_mp_global_discount',
                                                       raise_if_not_found=False)
        if mp_global_discount_product_tmpl:
            return mp_global_discount_product_tmpl.product_variant_id.id
        return False

    @api.model
    def _get_default_adjustment_product_id(self):
        mp_adjustment_product_tmpl = self.env.ref('izi_marketplace.product_tmpl_mp_adjustment',
                                                  raise_if_not_found=False)
        if mp_adjustment_product_tmpl:
            return mp_adjustment_product_tmpl.product_variant_id.id
        return False

    # @api.multi
    def generate_context(self):
        self.ensure_one()
        context = self._context.copy()
        context.update({
            'mp_account_id': self.id,
            'force_update': self.debug_force_update,
            'force_update_raw': self.debug_force_update_raw,
            'store_product_img': self.debug_store_product_img,
            'product_limit': self.debug_product_limit,
            'order_limit': self.debug_order_limit,
            'skip_error': self.debug_skip_error,
            'timezone': self._context.get('tz') or 'UTC',
        })
        return context

    # @api.multi
    def action_reauth(self):
        self.ensure_one()
        self.write({'state': 'authenticating'})

    # @api.multi
    def action_authenticate(self):
        self.ensure_one()
        if hasattr(self, '%s_authenticate' % self.marketplace):
            return getattr(self, '%s_authenticate' % self.marketplace)()

    # @api.multi
    def action_get_dependencies(self):
        self.ensure_one()
        if hasattr(self, '%s_get_dependencies' % self.marketplace):
            return getattr(self, '%s_get_dependencies' % self.marketplace)()

    # @api.multi
    def action_get_products(self, **kw):
        self.ensure_one()
        if hasattr(self, '%s_get_products' % self.marketplace):
            return getattr(self, '%s_get_products' % self.marketplace)(**kw)

    # @api.multi
    def action_map_product(self):
        product_map_obj = self.env['mp.map.product']

        self.ensure_one()

        product_map = product_map_obj.search([
            ('marketplace', '=', self.marketplace),
            ('mp_account_id', '=', self.id),
        ])

        if not product_map.exists():
            product_map = product_map_obj.create({
                'name': 'Product Mapping - %s' % self.name,
                'marketplace': self.marketplace,
                'mp_account_id': self.id,
            })

        action = self.env.ref('izi_marketplace.action_window_mp_map_product').read()[0]
        action.update({
            'res_id': product_map.id,
            'views': [(self.env.ref('izi_marketplace.form_mp_map_product').id, 'form')],
        })
        return action

    # @api.multi
    def action_view_mp_product(self):
        self.ensure_one()
        action = self.env.ref('izi_marketplace.action_window_mp_product_view_per_marketplace').read()[0]
        action.update({
            'domain': [('mp_account_id', '=', self.id)],
            'context': {
                'default_marketplace': self.marketplace,
                'default_mp_account_id': self.id
            }
        })
        return action

    def action_view_mp_orders(self):
        self.ensure_one()
        action = self.env.ref('izi_marketplace.action_window_mp_order_mp_account_order').read()[0]
        action.update({
            'domain': [('mp_account_id', '=', self.id)],
            'context': {
                'default_marketplace': self.marketplace,
                'default_mp_account_id': self.id,
                'default_company_id': self.company_id.id
            }
        })
        return action

    def action_view_mp_log_error(self):
        self.ensure_one()
        action = self.env.ref('izi_marketplace.action_window_mp_log_error').read()[0]
        action.update({
            'domain': [('mp_account_id', '=', self.id)]
        })
        return action

    def action_set_product(self, **kw):
        self.ensure_one()
        if hasattr(self, '%s_set_product' % self.marketplace):
            return getattr(self, '%s_set_product' % self.marketplace)(**kw)

    def auto_ship_orders(self, **kwargs):
        rec = self
        if kwargs.get('id', False):
            rec = self.browse(kwargs.get('id'))
        rec.ensure_one()
        if rec.auto_process_orders:
            if hasattr(rec, '%s_auto_ship_orders' % rec.marketplace):
                return getattr(rec, '%s_auto_ship_orders' % rec.marketplace)(**kwargs)


class IRCron(models.Model):
    _inherit = 'ir.cron'

    mp_account_id = fields.Many2one(comodel_name='mp.account', string='Marketplace Account', ondelete='cascade')
