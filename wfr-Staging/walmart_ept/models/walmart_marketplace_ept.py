import json
import logging
from calendar import monthrange
from datetime import date, datetime

from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

from odoo import models, fields, api, _
from ..walmart_api.walmart_call_api import Walmart

_logger = logging.getLogger("Walmart Instance")
_secondsConverter = {
    'days': lambda interval: interval * 24 * 60 * 60,
    'hours': lambda interval: interval * 60 * 60,
    'weeks': lambda interval: interval * 7 * 24 * 60 * 60,
    'minutes': lambda interval: interval * 60,
}


class WalmartMarketplace(models.Model):
    _name = 'walmart.marketplace.ept'
    _description = 'Walmart Marketplaces'

    @api.model
    def _get_default_walmart_auto_workflow(self):
        """
            This method is used to get default auto workflow for walmart marketpalce.
            @param None.
            @return: Get WorkFlow
        """
        try:
            return self.env.ref('common_connector_library.automatic_validation_ept')
        except ValueError:
            return False

    @api.model
    def _get_default_walmart_warehouse(self):
        """
            This method is used to get default warehouse for walmart marketplace.
            @param None.
            @return: Get Warehouse
        """
        stock_warehouse_obj = self.env['stock.warehouse']
        warehouse_id = stock_warehouse_obj.search(
            [('company_id', '=', self.env.user.company_id.id)], limit=1)
        return warehouse_id.id

    @api.model
    def _get_default_wfs_walmart_warehouse(self):
        """
            This method is used to get default warehouse for walmart marketplace.
            @param None.
            @return: Get Warehouse
        """
        stock_warehouse_obj = self.env['stock.warehouse']
        wfs_warehouse_id = stock_warehouse_obj.search(
            [('company_id', '=', self.env.user.company_id.id)], limit=1)
        return wfs_warehouse_id.id

    @api.model
    def _get_default_walmart_stock_field(self):
        """This method is used to get default stock filed value for walmart marketplace."""
        try:
            return self.env.ref('stock.field_product_product__virtual_available')
        except ValueError:
            return False

    @api.model
    def _get_default_walmart_shipment_fee(self):
        """
            This method is used to get default shipment fee for walmart marketplace.
            @param None.
            @return: Get Shipment Product
        """
        try:
            return self.env.ref('walmart_ept.product_product_walmart_shipment_fee')
        except ValueError:
            return False

    @api.model
    def _get_default_walmart_shipment_discount(self):
        """
            This method is used to get default shipment discount for walmart marketplace.
            @param None.
            @return: Get Shipment Discout Product
        """
        try:
            return self.env.ref('walmart_ept.product_product_walmart_shipment_discount')
        except ValueError:
            return False

    @api.model
    def _get_default_walmart_company_id(self):
        """
            This method is used to get default current user company for walmart marketplace.
            @param None.
            @return: Get Shipment Discout Product
        """
        return self.env.user.company_id

    @api.model
    def _get_default_walmart_payment_term(self):
        """
            This method is used to get default current user company for walmart marketplace.
            @param None.
            @return: Get Walmart Payment Term
        """
        try:
            return self.env.ref('account.account_payment_term_immediate')
        except ValueError:
            return False

    def _compute_count_all_walmart_orders(self):
        """
            This method return count for no of sale order that are in ['draft','confirm'] state.
            @param None.
            @return: Number of Orders
        """
        sale_order_obj = self.env['sale.order']
        for marketplace in self:
            quotation_orders = sale_order_obj.search(
                [('walmart_marketplace_id', '=', marketplace.id), ('state', 'in', ['draft'])])
            marketplace.quotation_count = len(quotation_orders) or False
            sent_saleorders = sale_order_obj.search(
                [('walmart_marketplace_id', '=', marketplace.id), ('state', 'in', ['sale'])])
            marketplace.order_count = len(sent_saleorders) or False

    @api.model
    def _get_default_stock_field(self):
        """
            This method Get Stock Field.
            @param None.
            @return: Stock Field
        """
        stock_field_id = self.env['ir.model.fields'].search(
            [('name', '=', 'qty_available'), ('model_id.model', '=', 'product.product')], limit=1)
        return stock_field_id.id if stock_field_id else False

    name = fields.Char()
    consumer_id = fields.Char(string="Consumer", help="Consumer Name")
    walmart_channel_type = fields.Char(string="Channel",
                                       default='0f3e4dd4-0514-4346-b39d-af0e00ea066d',
                                       help="Channel Type")
    walmart_secret_key = fields.Text(string="Walmart Secret Key", help="Secret Key")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse",
                                   default=_get_default_walmart_warehouse, help="Warehouse")
    wfs_warehouse_id = fields.Many2one('stock.warehouse', string="WFS Warehouse",
                                       default=_get_default_wfs_walmart_warehouse, help="Warehouse")
    is_selling_on_wfs = fields.Boolean("Are you selling on WFS? ", default=False,
                                       help="If it's checked, WFS Order will be Imported.")
    country_id = fields.Many2one('res.country', string="Country", help="Country")
    pricelist_id = fields.Many2one('product.pricelist', string="PriceList",
                                   help="Product PriceList")
    shipping_product_id = fields.Many2one('product.product', string="Shipping Product",
                                          domain=[('type', '=', 'service')],
                                          default=_get_default_walmart_shipment_fee,
                                          help="Shipping Product")
    discount_product_id = fields.Many2one('product.product', string="Discount Product",
                                          domain=[('type', '=', 'service')],
                                          default=_get_default_walmart_shipment_discount,
                                          help="Delivery Product")
    lang_id = fields.Many2one('res.lang', string="Language", help="Language")
    walmart_auto_workflow_id = fields.Many2one('sale.workflow.process.ept', string='Auto Workflow',
                                               default=_get_default_walmart_auto_workflow,
                                               help="Auto Invoice Workflow")
    last_sync_released_order_date = fields.Datetime(
        'Last Sync Order Date', help="It display on which last date \
        released orderes were imported")
    auto_create_product_not_found_in_odoo = fields.Boolean(
        'Auto Create Offer Not Found in Odoo', help="If it is ticked it will\
         automatically create offer[product] in odoo as well as in walmart")
    is_default_odoo_sequence_in_sales_order = fields.Boolean(
        'Is Default Odoo Sequence In Sale Order', default=True)
    order_prefix = fields.Char(size=10)
    company_id = fields.Many2one('res.company', string="Company",
                                 default=_get_default_walmart_company_id,
                                 help="Company of the User")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term',
                                      default=_get_default_walmart_payment_term,
                                      help="Payment Term for Doing Payment")
    quotation_ids = fields.One2many('sale.order', 'walmart_marketplace_id',
                                    domain=[('state', 'in', ['draft', 'sent'])],
                                    string="Quotations")
    quotation_count = fields.Integer(compute='_compute_count_all_walmart_orders',
                                     string="Quotations Order Count")
    order_ids = fields.One2many('sale.order', 'walmart_marketplace_id',
                                domain=[('state', 'not in', ['draft', 'sent', 'cancel'])],
                                string="Sales Order")
    order_count = fields.Integer(
        compute='_compute_count_all_walmart_orders', string="Sales Order Count")
    is_import_shipped_orders = fields.Boolean(help="Walmart Orders are Shipped Order not ")
    ship_order_start_date = fields.Datetime(string='ShipOrder Date',
                                            help='Date for importing Shipped Orders')
    auto_import_walmart_orders = fields.Boolean(
        help='It will automatically import orders by executing cron at a particular time interval.')

    auto_import_walmart_wfs_orders = fields.Boolean(
        help='It will automatically import WFS orders by executing cron at a particular time interval.')

    auto_import_walmart_wfs_inventory = fields.Boolean(
        help='It will automatically import WFS Inventory by executing cron at a particular time interval.')

    auto_import_walmart_reconciliation_report = fields.Boolean(
        help='It will automatically import reconciliation report by executing cron at a particular time interval.')

    # Added by Harshit Trivedi
    stock_field_id = fields.Many2one('ir.model.fields', string='Stock Field',
                                     default=_get_default_stock_field)
    state = fields.Selection([('not_confirmed', 'Not Confirmed'), ('confirmed', 'Confirmed')],
                             default='not_confirmed')
    last_inventory_export_date = fields.Datetime('Last Inventory Export Time',
                                                 help="Product Stock last Updated On ")
    last_wfs_inventory_import_date = fields.Datetime('Last WFS Inventory Import Time',
                                                     help="Product Stock last Updated On ")
    last_update_order_export_date = fields.Datetime('Last Order Update Time',
                                                    help="Order Status was last Updated On")
    order_auto_update = fields.Boolean(string="Auto Order Update ?")
    stock_auto_export = fields.Boolean(string="Auto Stock Export?")
    settlement_report_journal_id = fields.Many2one('account.journal',
                                                   string='Settlement Report Journal')
    auto_create_item_report_request = fields.Boolean()
    auto_process_item_report = fields.Boolean()
    update_product_image = fields.Boolean("Auto Update Product Image", default=False)
    create_product_inventory = fields.Boolean("Auto Create Product Inventory", default=False)
    location_id = fields.Many2one('stock.location', string="Inventory Location",
                                  domain=[('usage', '=', 'internal')])
    auto_create_refund = fields.Boolean("Auto Create Refund ?", default=True)
    auto_send_invoice = fields.Boolean("Auto Send Invoice via E-mail ?")
    auto_send_refund_invoice = fields.Boolean("Auto Send Refund Invoice via E-mail ?")
    team_id = fields.Many2one('crm.team', string='Sales Team')

    environment = fields.Selection([('sandbox', 'Sandbox'), ('production', 'Production')])
    walmart_tax_id = fields.Many2one('account.tax', string='Default Sales Tax')
    # Below fields use for the Dashboard
    color = fields.Integer(string='Color Index')
    walmart_order_data = fields.Text(compute="_compute_kanban_walmart_order_data")
    # Below field used for onboarding Panel
    is_instance_create_from_onboarding_panel = fields.Boolean(default=False)
    is_onboarding_configurations_done = fields.Boolean(default=False)
    active = fields.Boolean("Active", default=True)
    auto_apply_adjustments = fields.Boolean(string='Auto Apply Inventory Adjustments ?', default=False,
                                            help="If it is set, the quants will be applied automatically "
                                                 "while importing stock.")

    def _compute_kanban_walmart_order_data(self):
        if not self._context.get('sort'):
            context = dict(self.env.context)
            context.update({'sort': 'week'})
            self.env.context = context
        for record in self:
            # Prepare values for Graph
            values = record.get_graph_data(record)
            data_type, comparison_value = record.get_compare_data(record)
            # Total sales
            total_sales = round(sum([key['y'] for key in values]), 2)
            # Order count query
            order_data = record.get_total_orders()
            # Product count query
            product_data = record.get_total_products()
            # Customer count query
            customer_data = record.get_customers()
            # refund count query
            refund_data = record.get_refund()
            # Prepare shipped order
            order_shipped = record.get_shipped_orders()

            record.walmart_order_data = json.dumps({
                "values": values,
                "title": "",
                "key": "Order: Untaxed amount",
                "area": True,
                "color": "#875A7B",
                "is_sample_data": False,
                "total_sales": total_sales,
                "order_data": order_data,
                "product_date": product_data,
                "customer_data": customer_data,
                "order_shipped": order_shipped,
                "refund_data": refund_data,
                "refund_count": refund_data.get('refund_count'),
                "sort_on": self._context.get('sort'),
                "currency_symbol": record.company_id.currency_id.symbol or '',
                "graph_sale_percentage": {'type': data_type, 'value': comparison_value}
            })

    def get_graph_data(self, record):
        """
        Use: To get the details of walmart sale orders and total amount month wise or year wise to prepare the graph
        Task: 174853 - Walmart Dashboard
        Added by: Haresh Mori @Emipro Technologies on date 14 June 2021.
        :return: walmart sale order date or month and sum of sale orders amount of current instance
        """

        def get_current_week_date(record):
            self._cr.execute("""SELECT to_char(date(d.day),'DAY'), t.amount_untaxed as sum
                                FROM  (
                                   SELECT day
                                   FROM generate_series(date(date_trunc('week', (current_date)))
                                    , date(date_trunc('week', (current_date)) + interval '6 days')
                                    , interval  '1 day') day
                                   ) d
                                LEFT   JOIN 
                                (SELECT date(date_order)::date AS day, sum(amount_untaxed) as amount_untaxed
                                   FROM   sale_order
                                   WHERE  date(date_order) >= (select date_trunc('week', date(current_date)))
                                   AND    date(date_order) <= (select date_trunc('week', date(current_date)) 
                                   + interval '6 days')
                                   AND walmart_marketplace_id=%s and state in ('sale','done')
                                   GROUP  BY 1
                                   ) t USING (day)
                                ORDER  BY day""" % record.id)
            return self._cr.dictfetchall()

        def graph_of_current_month(record):
            self._cr.execute("""select EXTRACT(DAY from date(date_day)) :: integer,sum(amount_untaxed) from (
                        SELECT 
                          day::date as date_day,
                          0 as amount_untaxed
                        FROM generate_series(date(date_trunc('month', (current_date)))
                            , date(date_trunc('month', (current_date)) + interval '1 MONTH - 1 day')
                            , interval  '1 day') day
                        union all
                        SELECT date(date_order)::date AS date_day,
                        sum(amount_untaxed) as amount_untaxed
                          FROM   sale_order
                        WHERE  date(date_order) >= (select date_trunc('month', date(current_date)))
                        AND date(date_order)::date <= (select date_trunc('month', date(current_date)) 
                        + '1 MONTH - 1 day')
                        and walmart_marketplace_id = %s and state in ('sale','done')
                        group by 1
                        )foo 
                        GROUP  BY 1
                        ORDER  BY 1""" % record.id)
            return self._cr.dictfetchall()

        def graph_of_current_year(record):
            self._cr.execute("""select TRIM(TO_CHAR(DATE_TRUNC('month',month),'MONTH')),sum(amount_untaxed) from
                                (SELECT DATE_TRUNC('month',date(day)) as month,
                                  0 as amount_untaxed
                                FROM generate_series(date(date_trunc('year', (current_date)))
                                , date(date_trunc('year', (current_date)) + interval '1 YEAR - 1 day')
                                , interval  '1 MONTH') day
                                union all
                                SELECT DATE_TRUNC('month',date(date_order)) as month,
                                sum(amount_untaxed) as amount_untaxed
                                  FROM   sale_order
                                WHERE  date(date_order) >= (select date_trunc('year', date(current_date))) AND 
                                date(date_order)::date <= (select date_trunc('year', date(current_date)) 
                                + '1 YEAR - 1 day')
                                and walmart_marketplace_id = %s and state in ('sale','done')
                                group by DATE_TRUNC('month',date(date_order))
                                order by month
                                )foo 
                                GROUP  BY foo.month
                                order by foo.month""" % record.id)
            return self._cr.dictfetchall()

        def graph_of_all_time(record):
            self._cr.execute("""select TRIM(TO_CHAR(DATE_TRUNC('month',date_order),'YYYY-MM')),sum(amount_untaxed)
                                from sale_order where walmart_marketplace_id = %s and state in ('sale','done')
                                group by DATE_TRUNC('month',date_order) 
                                order by DATE_TRUNC('month',date_order)""" % record.id)
            return self._cr.dictfetchall()

        # Prepare values for Graph
        if self._context.get('sort') == 'week':
            result = get_current_week_date(record)
        elif self._context.get('sort') == "month":
            result = graph_of_current_month(record)
        elif self._context.get('sort') == "year":
            result = graph_of_current_year(record)
        else:
            result = graph_of_all_time(record)
        values = [{"x": ("{}".format(data.get(list(data.keys())[0]))), "y": data.get('sum') or 0.0} for data in result]
        return values

    def get_compare_data(self, record):
        """
        It is use to prepare Comparison ratio of orders.
        Task: 174853 - Walmart Dashboard
        Added by: Haresh Mori @Emipro Technologies on date 14 June 2021.
        :return: Comparison ratio of orders (weekly,monthly and yearly based on selection)
        """
        data_type = False
        total_percentage = 0.0

        def get_compared_week_data(record):
            current_total = 0.0
            previous_total = 0.0
            day_of_week = date.weekday(date.today())
            self._cr.execute("""select sum(amount_untaxed) as current_week from sale_order
                                where date(date_order) >= (select date_trunc('week', date(current_date))) and
                                walmart_marketplace_id=%s and state in ('sale','done')""" % record.id)
            current_week_data = self._cr.dictfetchone()
            if current_week_data:
                current_total = current_week_data.get('current_week') if current_week_data.get('current_week') else 0
            # Previous week data
            self._cr.execute("""select sum(amount_untaxed) as previous_week from sale_order
                            where date(date_order) between (select date_trunc('week', current_date) - interval '7 day') 
                            and (select date_trunc('week', (select date_trunc('week', current_date) - interval '7
                            day')) + interval '%s day')
                            and walmart_marketplace_id=%s and state in ('sale','done')
                            """ % (day_of_week, record.id))
            previous_week_data = self._cr.dictfetchone()
            if previous_week_data:
                previous_total = previous_week_data.get('previous_week') if previous_week_data.get(
                    'previous_week') else 0
            return current_total, previous_total

        def get_compared_month_data(record):
            current_total = 0.0
            previous_total = 0.0
            day_of_month = date.today().day - 1
            self._cr.execute("""select sum(amount_untaxed) as current_month from sale_order
                                where date(date_order) >= (select date_trunc('month', date(current_date)))
                                and walmart_marketplace_id=%s and state in ('sale','done')""" % record.id)
            current_data = self._cr.dictfetchone()
            if current_data:
                current_total = current_data.get('current_month') if current_data.get('current_month') else 0
            # Previous week data
            self._cr.execute("""select sum(amount_untaxed) as previous_month from sale_order where date(date_order)
                            between (select date_trunc('month', current_date) - interval '1 month') and
                            (select date_trunc('month', (select date_trunc('month', current_date) - interval
                            '1 month')) + interval '%s days')
                            and walmart_marketplace_id=%s and state in ('sale','done')
                            """ % (day_of_month, record.id))
            previous_data = self._cr.dictfetchone()
            if previous_data:
                previous_total = previous_data.get('previous_month') if previous_data.get('previous_month') else 0
            return current_total, previous_total

        def get_compared_year_data(record):
            current_total = 0.0
            previous_total = 0.0
            year_begin = date.today().replace(month=1, day=1)
            year_end = date.today()
            delta = (year_end - year_begin).days - 1
            self._cr.execute("""select sum(amount_untaxed) as current_year from sale_order
                                where date(date_order) >= (select date_trunc('year', date(current_date)))
                                and walmart_marketplace_id=%s and state in ('sale','done')""" % record.id)
            current_data = self._cr.dictfetchone()
            if current_data:
                current_total = current_data.get('current_year') if current_data.get('current_year') else 0
            # Previous week data
            self._cr.execute("""select sum(amount_untaxed) as previous_year from sale_order where date(date_order)
                            between (select date_trunc('year', date(current_date) - interval '1 year')) and 
                            (select date_trunc('year', date(current_date) - interval '1 year') + interval '%s days') 
                            and walmart_marketplace_id=%s and state in ('sale','done')
                            """ % (delta, record.id))
            previous_data = self._cr.dictfetchone()
            if previous_data:
                previous_total = previous_data.get('previous_year') if previous_data.get('previous_year') else 0
            return current_total, previous_total

        if self._context.get('sort') == 'week':
            current_total, previous_total = get_compared_week_data(record)
        elif self._context.get('sort') == "month":
            current_total, previous_total = get_compared_month_data(record)
        elif self._context.get('sort') == "year":
            current_total, previous_total = get_compared_year_data(record)
        else:
            current_total, previous_total = 0.0, 0.0
        if current_total > 0.0:
            if current_total >= previous_total:
                data_type = 'positive'
                total_percentage = (current_total - previous_total) * 100 / current_total
            if previous_total > current_total:
                data_type = 'negative'
                total_percentage = (previous_total - current_total) * 100 / current_total
        return data_type, round(total_percentage, 2)

    def get_total_orders(self):
        """
        To get the list of walmart sale orders month wise or year wise
        Task: 174853 - Walmart Dashboard
        Added by: Haresh Mori @Emipro Technologies on date 14 June 2021.
        :return: total number of walmart sale orders ids and action for sale orders of current instance
        """
        order_query = """select id from sale_order where walmart_marketplace_id= %s and state in ('sale','done')""" % \
                      self.id

        def orders_of_current_week(order_query):
            qry = order_query + """ and date(date_order) >= (select date_trunc('week', date(current_date))) order by 
            date(date_order)"""
            self._cr.execute(qry)
            return self._cr.dictfetchall()

        def orders_of_current_month(order_query):
            qry = order_query + """ and date(date_order) >=(select date_trunc('month', date(current_date))) order by 
            date(date_order)"""
            self._cr.execute(qry)
            return self._cr.dictfetchall()

        def orders_of_current_year(order_query):
            qry = order_query + """ and date(date_order) >= (select date_trunc('year', date(current_date))) order by 
            date(date_order)"""
            self._cr.execute(qry)
            return self._cr.dictfetchall()

        def orders_of_all_time(record):
            self._cr.execute(
                """select id from sale_order where walmart_marketplace_id = %s and state in ('sale','done')""" % (
                    record.id))
            return self._cr.dictfetchall()

        order_data = {}
        if self._context.get('sort') == "week":
            result = orders_of_current_week(order_query)
        elif self._context.get('sort') == "month":
            result = orders_of_current_month(order_query)
        elif self._context.get('sort') == "year":
            result = orders_of_current_year(order_query)
        else:
            result = orders_of_all_time(self)
        order_ids = [data.get('id') for data in result]
        view = self.env.ref('walmart_ept.action_walmart_sales_order_ept').sudo().read()[0]
        action = self.prepare_action(view, [('id', 'in', order_ids)])
        order_data.update({'order_count': len(order_ids), 'order_action': action})
        return order_data

    def get_total_products(self):
        """
        To get the list of products exported from walmart instance
        Task: 174853 - Walmart Dashboard
        Added by: Haresh Mori @Emipro Technologies on date 14 June 2021.
        :return: total number of walmart products ids and action for products
        """
        product_data = {}
        self._cr.execute("""select count(id) as total_count from walmart_offer_ept where
                        marketplace_id = %s""" % self.id)
        result = self._cr.dictfetchall()
        if result:
            total_count = result[0].get('total_count')
        view = self.env.ref('walmart_ept.action_walmart_marketplace_offers_tree_ept').sudo().read()[0]
        action = self.prepare_action(view, [('marketplace_id', '=', self.id)])
        product_data.update({'product_count': total_count, 'product_action': action})
        return product_data

    def get_customers(self):
        """
        To get the list of customers with walmart instance for current walmart instance
        Task: 174853 - Walmart Dashboard
        Added by: Haresh Mori @Emipro Technologies on date 14 June 2021.
        :return: total number of customer ids and action for customers
        """
        customer_data = {}
        self._cr.execute("""select id from res_partner where walmart_instance_id = %s and 
        is_walmart_customer = True""" % self.id)
        result = self._cr.dictfetchall()
        customer_ids = [data.get('id') for data in result]
        view = self.env.ref('walmart_ept.walmart_res_partner_action').sudo().read()[0]
        action = self.prepare_action(view, [('id', 'in', customer_ids), ('active', 'in', [True, False])])
        customer_data.update({'customer_count': len(customer_ids), 'customer_action': action})
        return customer_data

    def get_refund(self):
        """
        Use: To get the list of refund orders of walmart instance for current walmart instance
        Task: 174853 - Walmart Dashboard
        Added by: Haresh Mori @Emipro Technologies on date 14 June 2021.
        :return: total number of refund order ids and action for customers
        """
        refund_query = """select id from walmart_order_refund_ept where instance_id=%s""" % self.id

        def refund_of_current_week(refund_query):
            qry = refund_query + " and date(create_date) >= (select date_trunc('week', date(current_date)))"
            self._cr.execute(qry)
            return self._cr.dictfetchall()

        def refund_of_current_month(refund_query):
            qry = refund_query + " and date(create_date) >= (select date_trunc('month', date(current_date)))"
            self._cr.execute(qry)
            return self._cr.dictfetchall()

        def refund_of_current_year(refund_query):
            qry = refund_query + " and date(create_date) >= (select date_trunc('year', date(current_date)))"
            self._cr.execute(qry)
            return self._cr.dictfetchall()

        def refund_of_all_time(refund_query):
            self._cr.execute(refund_query)
            return self._cr.dictfetchall()

        refund_data = {}
        if self._context.get('sort') == "week":
            result = refund_of_current_week(refund_query)
        elif self._context.get('sort') == "month":
            result = refund_of_current_month(refund_query)
        elif self._context.get('sort') == "year":
            result = refund_of_current_year(refund_query)
        else:
            result = refund_of_all_time(refund_query)
        refund_ids = [data.get('id') for data in result]
        view = self.env.ref('walmart_ept.walmart_order_refund_main_action_ept').sudo().read()[0]
        action = self.prepare_action(view, [('id', 'in', refund_ids)])
        refund_data.update({'refund_count': len(refund_ids), 'refund_action': action})
        return refund_data

    def get_shipped_orders(self):
        """
        Use: To get the list of shopify shipped orders month wise or year wise
        return: total number of walmart shipped orders ids and action for shipped orders of current instance
        """
        shipped_query = """select so.id from stock_picking sp
                             inner join sale_order so on so.procurement_group_id=sp.group_id inner 
                             join stock_location on stock_location.id=sp.location_dest_id and stock_location.usage='customer' 
                             where sp.updated_in_walmart = True and sp.state != 'cancel' and 
                             so.walmart_marketplace_id=%s""" % self.id

        def shipped_order_of_current_week(shipped_query):
            qry = shipped_query + " and date(so.date_order) >= (select date_trunc('week', date(current_date)))"
            self._cr.execute(qry)
            return self._cr.dictfetchall()

        def shipped_order_of_current_month(shipped_query):
            qry = shipped_query + " and date(so.date_order) >= (select date_trunc('month', date(current_date)))"
            self._cr.execute(qry)
            return self._cr.dictfetchall()

        def shipped_order_of_current_year(shipped_query):
            qry = shipped_query + " and date(so.date_order) >= (select date_trunc('year', date(current_date)))"
            self._cr.execute(qry)
            return self._cr.dictfetchall()

        def shipped_order_of_all_time(shipped_query):
            self._cr.execute(shipped_query)
            return self._cr.dictfetchall()

        order_data = {}
        if self._context.get('sort') == "week":
            result = shipped_order_of_current_week(shipped_query)
        elif self._context.get('sort') == "month":
            result = shipped_order_of_current_month(shipped_query)
        elif self._context.get('sort') == "year":
            result = shipped_order_of_current_year(shipped_query)
        else:
            result = shipped_order_of_all_time(shipped_query)
        order_ids = [data.get('id') for data in result]
        view = self.env.ref('walmart_ept.action_walmart_sales_order_ept').sudo().read()[0]
        action = self.prepare_action(view, [('id', 'in', order_ids)])
        order_data.update({'order_count': len(order_ids), 'order_action': action})
        return order_data

    def prepare_action(self, view, domain):
        """
        Use: To prepare action dictionary
        Task: 174853 - Walmart Dashboard
        Added by: Haresh Mori @Emipro Technologies on date 14 June 2021.
        :return: action details
        """
        action = {
            'name': view.get('name'),
            'type': view.get('type'),
            'domain': domain,
            'view_mode': view.get('view_mode'),
            'view_id': view.get('view_id')[0] if view.get('view_id') else False,
            'views': view.get('views'),
            'res_model': view.get('res_model'),
            'target': view.get('target'),
        }

        if 'tree' in action['views'][0]:
            action['views'][0] = (action['view_id'], 'list')
        return action

    @api.model
    def perform_operation(self, record_id):
        """
        To prepare walmart operation action
        Task: 174853 - Walmart Dashboard
        Added by: Haresh Mori @Emipro Technologies on date 14 June 2021.
        :return: walmart operation action details
        """
        view = self.env.ref('walmart_ept.action_wizard_walmart_import_export_operations_for_kanban').sudo().read()[0]
        action = self.prepare_action(view, [])
        action.update({'context': {'default_marketplace_id': record_id}})
        return action

    @api.model
    def open_report(self, record_id):
        """
        To prepare walmart report action
        Task: 174853 - Walmart Dashboard
        Added by: Haresh Mori @Emipro Technologies on date 14 June 2021.
        :return: walmart report action details
        """
        view = self.env.ref('walmart_ept.walmart_sale_report_action_dashboard').sudo().read()[0]
        action = self.prepare_action(view, [('walmart_marketplace_id', '=', record_id)])
        action.update({'context': {'search_default_walmart_marketplace': record_id, 'search_default_Sales': 1,
                                   'search_default_filter_date': 1}})
        return action

    @api.model
    def open_logs(self, record_id):
        """
        To prepare walmart logs action
        Task: 174853 - Walmart Dashboard
        Added by: Haresh Mori @Emipro Technologies on date 14 June 2021.
        :return: walmart logs action details
        """
        view = self.env.ref('walmart_ept.action_walmart_log_book_ept').sudo().read()[0]
        return self.prepare_action(view, [('walmart_marketplace_id', '=', record_id)])

    def update_changes(self):
        """
            This method update the changes done in walmart credentials button
            @param None.
            @return: Update Walmart Details
        """
        country_currency = self.country_id.currency_id.id or False
        pricelist_currency = self.pricelist_id.currency_id.id or False
        if country_currency != pricelist_currency:
            raise ValidationError(_('Country Currency and Pricelist Currency does not matched..!'))
        return True

    def show_walmart_credential(self):
        """
            This method returns form view of walmart credentials,
            through which user can see the credentials of walmart marketplace
            as well it can also update it.
            @param None.
            @return: Show Walmart Credential

        """
        form = self.env.ref('walmart_ept.walmart_marketplace_credential_form', False)
        return {'name': _('Walmart Details'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'walmart.marketplace.ept',
                'view_id': form.id,
                'nodestroy': True,
                'target': 'new',
                'context': {},
                'res_id': self and self.ids[0] or False}

    def confirm(self):
        """
            Change the Walmart Instance Set To Confirm
            @param None.
            @return: Change the Walmart Instance State
        """
        if self.state != 'confirmed':
            try:
                conn_obj = self.get_walmart_connection()
                if conn_obj:
                    self.write({'state': 'confirmed'})
            except Exception as err:
                raise ValidationError(err)
        return True

    def reset_to_confirm(self):
        """
            Reset the Walmart Confirmation Instance
            @param None.
            @return: Instance back to Confirm Details
        """
        self.write({'state': 'not_confirmed'})
        return True

    # -----Cron Method-------------------------------------------------------------------------
    @api.model
    def auto_update_order_status_ept(self, **args):
        """
            Cron for the Update Order Status in Walmart
            @param: Args it is pass the Walmart Instance .
            @return: True
        """
        instance_id = args.get('instance_id')
        sale_order_obj = self.env['sale.order']
        if instance_id:
            instances = self.browse(instance_id)
            for instance in instances:
                sale_order_obj.walmart_update_order_status(instance)
                instance.write({'last_update_order_export_date': datetime.now()})
        return True

    @api.model
    def auto_export_inventory_ept(self, **args):
        """
            Cron for the Export Inventory in Walmart
            @param: In Args it is pass the Walmart Instance .
            @return: True
        """
        instance_id = args.get('instance_id')
        walmart_product_obj = self.env['walmart.offer.ept']
        if instance_id:
            instances = self.browse(instance_id)
            for instance in instances:
                walmart_product_obj.export_stock_in_walmart(instance)
                instance.write({'last_inventory_export_date': datetime.now()})
        return True

    # @api.model
    # def auto_get_item_report_ept(self, **args):
    #     """
    #         Cron for the Get Product (item) Report From Walmart
    #         @param In Args it is pass the Walmart Instance .
    #         @return: True
    #     """
    #     instance_id = args.get('instance_id')
    #     walmart_product_obj = self.env['walmart.offer.ept']
    #     if instance_id:
    #         instances = self.browse(instance_id)
    #         for instance in instances:
    #             walmart_product_obj.walmart_get_item_report_ept(instance,
    #                                                             instance.update_product_image,
    #                                                             instance.create_product_inventory,
    #                                                             instance.location_id)
    #
    #     return True

    @api.model
    def auto_import_walmart_orders_via_cron(self, **args):
        """
            Cron for the Import Order Related Walmart
            @param: In Args it is pass the Walmart Instance .
            @return: True
        """
        sale_order_obj = self.env['sale.order']
        marketplace_id = args.get('marketplace_id', False)
        marketplace_id = marketplace_id and self.search(
            [('id', '=', marketplace_id), ('state', '=', 'confirmed')])
        if marketplace_id:
            sale_order_obj.import_walmart_orders(
                marketplace_id, order_status='Created', start_date='', end_date='')
            marketplace_id.write({'last_sync_released_order_date': datetime.now()})
        return True

    @api.model
    def auto_import_walmart_wfs_orders_via_cron(self, **args):
        """
            Cron for the Import WFS Order Related Walmart
            @param: In Args it is pass the Walmart Instance .
            @return: True
        """
        sale_order_obj = self.env['sale.order']
        marketplace_id = args.get('marketplace_id', False)
        marketplace_id = marketplace_id and self.search(
            [('id', '=', marketplace_id), ('state', '=', 'confirmed')])
        if marketplace_id:
            sale_order_obj.import_walmart_orders(
                marketplace_id, order_status='Created', start_date='', end_date='')
            marketplace_id.write({'last_sync_released_order_date': datetime.now()})
        return True

    @api.model
    def auto_import_walmart_wfs_inventory_via_cron(self, **args):
        """
        Cron for the Import WFS Inventory Related Walmart
        :param args: dict {}
        :return: True
        """
        walmart_product_obj = self.env['walmart.offer.ept']
        marketplace_id = args.get('ctx', {}).get('walmart_instance_id', False)
        marketplace_id = marketplace_id and self.search([('id', '=', marketplace_id)], limit=1)
        if marketplace_id:
            walmart_product_obj.import_wfs_inventory(
                marketplace_id, marketplace_id.auto_apply_adjustments)
            marketplace_id.write({'last_wfs_inventory_import_date': datetime.now()})
        return True

    @api.model
    def auto_send_invoice_via_cron(self):
        """
            Cron for the Send Invoice in Walmart
            @param In Args it is pass the Walmart Instance .
            @return: True
        """
        walmart_invoice = self.env['account.move']
        instances = self.search([('auto_send_invoice', '=', True)])
        for instance in instances:
            walmart_invoice.get_instance_invoice(instance)

        return True

    @api.model
    def auto_send_refund_invoice_via_cron(self):
        """
            Cron for the Send Refund Invoice in Walmart
            @param In Args it is pass the Walmart Instance .
            @return: True
        """
        walmart_invoice = self.env['account.move']
        instances = self.search(
            [('auto_send_refund_invoice', '=', True)])
        for instance in instances:
            walmart_invoice.get_instance_refund_invoice(instance)

        return True

    def cron_configuration_action(self):
        """
        Cron Configuration Action
        :return: Cron Configuration Action
        """
        action = self.env.ref('walmart_ept.action_wizard_walmart_cron_configuration_ept').read()[0]
        view_id = self.env.ref('walmart_ept.walmart_cron_configuration_ept_form_view')
        action_data = {'view_id': view_id.id, 'views': [(view_id.id, 'form')], 'target': 'new',
                       'name': 'Cron Configuration'}
        context = {'walmart_marketplace_id': self.id}
        action['context'] = context
        action.update(action_data)
        return action

    def get_walmart_connection(self):
        """
        Preparing Connection Object
        :return: Walmart Connection
        """
        return Walmart(client_id=self.consumer_id, client_secret=self.walmart_secret_key,
                       environment=self.environment,country_code=self.country_id.code.lower())

    def search_walmart_marketplace(self):
        """ This method used to search the marktplace.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 28 June 2021 .
            Task_id: 176151 - Walmart Panel
        """
        company = self.env.user.company_id or self.env.company
        instance = self.search(
            [('is_instance_create_from_onboarding_panel', '=', True),
             ('is_onboarding_configurations_done', '=', False),
             ('company_id', '=', company.id)], limit=1, order='id desc')
        if not instance:
            instance = self.search([('company_id', '=', company.id),
                                    ('is_onboarding_configurations_done', '=', False)],
                                   limit=1, order='id desc')
            instance.write({'is_instance_create_from_onboarding_panel': True})
        return instance

    def get_walmart_cron_execution_time(self, cron_name):
        """
        This method is used to get the interval time of the cron.
        @param cron_name: External ID of the Cron.
        @return: Interval time in seconds.
        @author: Maulik Barad on Date 25-Nov-2020.
        """
        process_queue_cron = self.env.ref(cron_name, False)
        if not process_queue_cron:
            raise UserError(_("Please upgrade the module. \n Maybe the job has been deleted, it will be recreated at "
                              "the time of module upgrade."))
        interval = process_queue_cron.interval_number
        interval_type = process_queue_cron.interval_type
        if interval_type == "months":
            days = 0
            current_year = fields.Date.today().year
            current_month = fields.Date.today().month
            for i in range(0, interval):
                month = current_month + i

                if month > 12:
                    if month == 13:
                        current_year += 1
                    month -= 12

                days_in_month = monthrange(current_year, month)[1]
                days += days_in_month

            interval_type = "days"
            interval = days
        interval_in_seconds = _secondsConverter[interval_type](interval)
        return interval_in_seconds

    def action_redirect_to_ir_cron(self):
        """
        Redirect to ir.cron model with cron name like Walmart
        :return:  action
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd.
        """
        action = self.env.ref('base.ir_cron_act').read()[0]
        action['domain'] = [('name', 'ilike', self.name), ('name', 'ilike', 'walmart'), ('active', '=', True)]
        return action

    def action_walmart_active_archive_instance(self):
        """
        This method is used to open a wizard to display the information related to how many data will be
        archived/deleted while instance Active/Archive.
        @author: Nikul Alagiya on Date 29/01/2022.
        """
        view = self.env.ref('walmart_ept.view_active_archive_walmart_instance')
        return {
            'name': _('Instance Active/Archive Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'walmart.queue.process.ept',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': self._context,
        }

    def change_auto_cron_status(self):
        """
        After connect or disconnect the walmart instance disable all the Scheduled Actions.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd.
        """
        try:
            stock_cron_exist = self.env.ref('walmart_ept.ir_cron_auto_export_inventory_instance_%d' % self.id)
        except Exception as error:
            stock_cron_exist = False
            _logger.info(error)
        try:
            order_cron_exist = self.env.ref('walmart_ept.ir_cron_auto_import_walmart_orders_instance_%d' % self.id)
        except Exception as error:
            order_cron_exist = False
            _logger.info(error)
        try:
            wfs_order_cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_import_walmart_wfs_orders_instance_%d' % self.id)
        except Exception as error:
            wfs_order_cron_exist = False
            _logger.info(error)
        try:
            wfs_inventory_cron_exist = self.env.ref(
                'walmart_ept.ir_cron_auto_import_walmart_wfs_inventory_instance_%d' % self.id)
        except Exception as error:
            wfs_inventory_cron_exist = False
            _logger.info(error)
        try:
            order_status_cron_exist = self.env.ref(
                'walmart_ept.ir_cron_update_order_status_instance_%d' % self.id)
        except Exception as error:
            order_status_cron_exist = False
            _logger.info(error)

        if stock_cron_exist:
            stock_cron_exist.write({'active': False})
        if order_cron_exist:
            order_cron_exist.write({'active': False})
        if wfs_order_cron_exist:
            wfs_order_cron_exist.write({'active': False})
        if wfs_inventory_cron_exist:
            wfs_inventory_cron_exist({'active': False})
        if order_status_cron_exist:
            order_status_cron_exist.write({'active': False})

    def walmart_action_archive_unarchive(self):
        """
        This method used to active and unarchive instance and base on the active/unarchive instance-related
        data also, archive/unarchive.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 29/01/2022.
        """
        domain = [("walmart_marketplace_id", "=", self.id)]
        if self.active:
            activate = {"active": False}

            self.write(activate)
            self.change_auto_cron_status()
        else:
            self.get_walmart_connection()
            activate = {"active": True}
            domain.append(("active", "=", False))
            self.write(activate)

        return True

    @api.model
    def auto_import_walmart_reconciliation_report_ept(self, **args):
        """
        Define this method for auto import reconciliation report.
        :param args: dict {}
        :return: True
        """
        walmart_reconciliation_report_obj = self.env['walmart.reconciliation.report.ept']
        marketplace_id = args.get('ctx', {}).get('walmart_instance_id', False)
        marketplace_id = marketplace_id and self.search([('id', '=', marketplace_id)], limit=1)
        if marketplace_id:
            walmart_reconciliation_report_obj.with_context(is_auto_process=True).get_walmart_report_date(marketplace_id)
        return True

    @api.model
    def auto_process_walmart_reconciliation_report_ept(self, **args):
        """
        Define this method for auto process reconciliation report.
        :param args: dict {}
        :return: True
        """
        walmart_reconciliation_report_obj = self.env['walmart.reconciliation.report.ept']
        marketplace_id = args.get('ctx', {}).get('walmart_instance_id', False)
        marketplace_id = marketplace_id and self.search([('id', '=', marketplace_id)], limit=1)
        if marketplace_id:
            reconciliation_reports = walmart_reconciliation_report_obj.search([
                ('marketplace_id', '=', marketplace_id.id), ('state', 'in', ('draft', 'done'))])
            for report in reconciliation_reports:
                if not report.attachment_id and report.state == 'draft':
                    report.with_context(is_auto_process=True).get_reconciliation_report_ept()
                if report.attachment_id and report.state == 'done':
                    report.with_context(is_auto_process=True).process_settlement_report_file()
                report._cr.commit()
        return True
