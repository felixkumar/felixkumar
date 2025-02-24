from odoo import api, fields, models, _


class SaleReportInherit(models.Model):
    _inherit = "sale.report"

    sales_channel_id = fields.Many2one(comodel_name='sales.channel', string="Sales Channel", readonly=True)

    def _select_sale(self):
        res = super(SaleReportInherit, self)._select_sale()
        res += ', sc.id AS sales_channel_id'
        return res

    def _group_by_sale(self):
        return super(SaleReportInherit, self)._group_by_sale() + """
                    ,sc.id
                """

    def _from_sale(self):
        return super(SaleReportInherit, self)._from_sale() + """
            LEFT JOIN crm_team ct ON ct.id = s.team_id
            LEFT JOIN sales_channel sc ON sc.id = ct.sales_channel_id
                        """
