from odoo import fields, models
import odoo


class SaleReport(models.Model):
    _inherit = "sale.report"

    walmart_marketplace_id = fields.Many2one("walmart.marketplace.ept", "Walmart Marketplace",
                                          copy=False, readonly=True)

    def _select_additional_fields(self):
        """
         Inherited Select method to Add Walmart fields filter in Reports
        :return: 
        """
        res = super(SaleReport, self)._select_additional_fields()
        res['walmart_marketplace_id'] = "s.walmart_marketplace_id"
        return res

    def _group_by_sale(self):
        group_by_ = super(SaleReport, self)._group_by_sale()
        group_by_ += ", s.walmart_marketplace_id"
        return group_by_

    def walmart_sale_report(self):
        """
            Base on the odoo version it return the action.
        """
        version_info = odoo.service.common.exp_version()
        if version_info.get('server_version') == '14.0':
            action = self.env.ref('walmart_ept.walmart_action_order_report_all').read()[0]
        else:
            action = self.env.ref('walmart_ept.walmart_sale_report_action_dashboard').read()[0]

        return action
