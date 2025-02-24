from odoo import api, fields, models
from odoo import tools


# overdue report model
class Overdue_report(models.Model):
    _name = "overdue.report"
    _description = "Overdue Report"
    _auto = False
    _rec_name = 'partner_id'
    _order = 'date desc'

    date = fields.Date('Date Order', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner Id', readonly=True)
#     credit = fields.Float('Credit', readonly=True)
    name = fields.Char('Name')
    date_maturity = fields.Date('Due Date', readonly=True)
    ref = fields.Char(string='Reference')
    residual = fields.Float(string='Due Amount')
    # overdue report data with query
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
        SELECT
             aml.id as id,
             aml.date_invoice as date,
             aml.partner_id as partner_id,
             aml.number as ref,
             aml.name as name,
             sum(aml.residual) as residual,
             aml.date_due as date_maturity
        FROM
             account_invoice as aml
        INNER JOIN res_partner rp ON rp.id =  aml.partner_id
        INNER JOIN account_account aa on aa.id=aml.account_id 
        WHERE
         aa.deprecated=false and aa.internal_type = 'receivable' and aml.residual != 0.0
        GROUP BY aml.id,aml.date,aml.move_id,aml.partner_id,aml.number,aml.date_due ,aml.name )"""
                            % (self._table,))
