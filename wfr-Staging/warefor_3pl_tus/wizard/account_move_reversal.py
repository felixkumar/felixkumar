# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    @api.model
    def default_get(self, fields):
        res = {}
        if self.env.context.get('active_model') == 'custom.credit.memo.wizard':
            wizard_id = self.env['custom.credit.memo.wizard'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'custom.credit.memo.wizard' else self.env['custom.credit.memo.wizard']
            move_ids = wizard_id.invoice_id
            if any(move.state != "posted" for move in move_ids):
                raise UserError(_('You can only reverse posted moves.'))
            if 'company_id' in fields:
                res['company_id'] = move_ids.company_id.id or self.env.company.id
            if 'move_ids' in fields:
                res['move_ids'] = [(6, 0, move_ids.ids)]
            if 'refund_method' in fields:
                res['refund_method'] = (len(move_ids) > 1 or move_ids.move_type == 'entry') and 'cancel' or 'refund'
        else:
            res = super(AccountMoveReversal, self).default_get(fields)
        return res

    def reverse_moves(self):
        res = super(AccountMoveReversal, self).reverse_moves()
        if len(self.move_ids) == 1 and self.move_ids.freight_id and res.get('res_id'):
            self.move_ids.freight_id.account_move_ids = [(4, res.get('res_id'))]
        return res
