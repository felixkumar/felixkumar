from odoo import models

class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    def _run_action_code_multi(self, eval_context):
        res = super()._run_action_code_multi(eval_context)
        if self._context.get('is_edi_export'):
            res = eval_context.get('edi_value')
        return res
