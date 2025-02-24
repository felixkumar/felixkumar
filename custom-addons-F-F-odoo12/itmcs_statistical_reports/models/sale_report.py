from odoo import models, fields, api, tools
from odoo.addons import decimal_precision as dp

class SaleReport(models.Model):
    _inherit = "sale.report"

    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    purchase_price = fields.Float('Cost Price', required=True, digits=dp.get_precision('Cost Price'), default=0.0)
    gross_profit = fields.Float('Gross Profit', required=True, digits=dp.get_precision('Gross profit'), default=0.0)
    margin = fields.Float('Margin %', required=True, digits=(10, 3), default=0.0)
    avg_cost = fields.Float('Avg Cost', required=True, digits=dp.get_precision('Avg Cost'), default=0.0,invisible=True)
    avg_margin = fields.Float('Avg Margin', required=True, digits=dp.get_precision('Avg Margin'), default=0.0,invisible=True)
    avg_unit_price = fields.Float('Avg Price Unit', required=True, digits=dp.get_precision('Avg Price Unit'), default=0.0,invisible=True)
    standard_price = fields.Float('Cost', required=True, digits=dp.get_precision('Cost'), default=0.0)
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse")


    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(l.id) as id,
            l.product_id as product_id,
            t.uom_id as product_uom,
            sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
            sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
            sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
            sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
            sum(l.price_total / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_total,
            sum(l.price_subtotal / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_subtotal,
            sum(l.untaxed_amount_to_invoice / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as untaxed_amount_to_invoice,
            sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as untaxed_amount_invoiced,
            count(*) as nbr,
            s.name as name,
            s.date_order as date,
            s.confirmation_date as confirmation_date,
            s.state as state,
            s.partner_id as partner_id,
            s.user_id as user_id,
            s.company_id as company_id,
            extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
            t.categ_id as categ_id,
            s.pricelist_id as pricelist_id,
            s.analytic_account_id as analytic_account_id,
            s.team_id as team_id,
            p.product_tmpl_id,
            partner.country_id as country_id,
            partner.commercial_partner_id as commercial_partner_id,
            sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
            sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume,
            l.discount as discount,
            sum((l.price_unit * l.product_uom_qty * l.discount / 100.0 / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END)) as discount_amount,
            s.id as order_id
        """
        select_ += """
                ,s.warehouse_id as warehouse_id,
                t.standard_price as standard_price,
                sum(l.price_unit) as price_unit ,
                sum(l.purchase_price) as purchase_price , 
               case when l.price_unit > 0 then
                    ((l.price_unit - coalesce(t.standard_price ,0)) * sum(product_uom_qty))/ (l.price_unit * sum(product_uom_qty))* 100 end as margin, 
               ((l.price_unit - coalesce(t.standard_price ,0) ) * sum(product_uom_qty))  as gross_profit,
               case when l.qty_invoiced > 0 then
               sum(t.standard_price * l.qty_invoiced)
               else 0 end as avg_cost,
               case when l.qty_invoiced > 0 then
               1-sum(t.standard_price*l.qty_invoiced)/sum(l.qty_invoiced) 
               else 0 end as avg_margin,
               case when l.qty_invoiced > 0 then
               sum(l.price_unit * l.qty_invoiced)/sum(l.qty_invoiced)
               else 0 end as avg_unit_price           
               """

        for field in fields.values():
            select_ += field

        from_ = """
                sale_order_line l
                      join sale_order s on (l.order_id=s.id)
                      join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom u on (u.id=l.product_uom)
                    left join uom_uom u2 on (u2.id=t.uom_id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
                %s
        """ % from_clause
        where_ ="""

            l.product_id IS NOT NULL
        """
        groupby_ = """
            l.product_id,
            l.order_id,
            t.uom_id,
            t.categ_id,
            s.name,
            s.date_order,
            s.confirmation_date,
            s.partner_id,
            s.user_id,
            s.state,
            s.company_id,
            s.pricelist_id,
            s.analytic_account_id,
            s.team_id,
            p.product_tmpl_id,
            partner.country_id,
            partner.commercial_partner_id,
            l.discount,
            s.warehouse_id,
            s.id %s
        """% (groupby)
        groupby_ += """
                ,l.price_unit,
                l.purchase_price,
                t.standard_price,
                l.qty_invoiced
                """

        return '%s (SELECT %s FROM %s WHERE %s GROUP BY %s)' % (with_, select_, from_, where_,groupby_)

    class ProductTemplate(models.Model):
        _inherit = 'product.template'

        standard_price = fields.Float(
            'Cost', compute='_compute_standard_price',
            inverse='_set_standard_price', search='_search_standard_price',
            digits=dp.get_precision('Product Price'), groups="base.group_user",
            help="Cost used for stock valuation in standard price and as a first price to set in average/FIFO.",
            store=True)
