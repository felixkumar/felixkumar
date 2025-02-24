# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'


    @api.model
    def get_paperformat(self):
        res = super(IrActionsReport, self).get_paperformat()
        res_ids = self._context.get('res_ids')
        is_oxford = [False]
        if res_ids and self.binding_model_id.model == 'account.move':
            res_ids = self.env['account.move'].browse(res_ids)
            is_oxford = res_ids.mapped('company_id').mapped('is_oxford')
        if True in is_oxford:
            return self.env.ref('extended_invoice_template_tus.account_custom_customer_invoice_paperformat_oxf')
        else:
            return res

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        return super(IrActionsReport, self.with_context(res_ids=res_ids))._render_qweb_pdf(report_ref=report_ref, res_ids=res_ids, data=data)
