# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, float_compare
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=[('account_review', 'Account Review')])

    @api.multi
    def action_confirm(self):
        Params = self.env['ir.config_parameter'].sudo()

        on_exceeded = Params.get_param('partner_credit_limit.on_exceeded') or False
        use_global_limit = Params.get_param('partner_credit_limit.use_global_limit') or False
        global_limit = float(Params.get_param('partner_credit_limit.global_limit')) or 0.0
       
        for order in self:
            this_credit_limit = this_credit_to_compare = 0.0
            #Check if this_partner has a parent entity.
            #If id does, move to parent anyway.
            this_partner = order.partner_id.parent_id or order.partner_id

            #Credit limit with partner first if we apply_individual_credit_limit on this partner. 
            if this_partner.apply_individual_credit_limit:
                this_credit_limit = this_partner.credit_limit

            #See if we use a global credit limit.
            if use_global_limit:
                #Credit limit go with the global limit.
                this_credit_limit = global_limit


            #The amount we compare credit to.
            this_credit_to_compare = order.amount_total


            #See if we count in the uninvoiced amount.
            
            #Count in credit in account app this partner already has.
            this_credit_to_compare += this_partner.credit

            #Credits do exceeded.
            if this_credit_limit > 0 and this_credit_to_compare > this_credit_limit:
                if on_exceeded == 'raise_exception':
                    #We raise exception
                    msg = _("""The partner %s 's credit limit has been exceeded. Please review.""") % this_partner.name
                    raise UserError(_('Credit Limit Exceeded') + '\n' + msg)
                elif on_exceeded == 'leave_undecided':
                    order.write({'state': 'account_review'})
            else:
                #Do normal stuff.
                super(SaleOrder, order).action_confirm()
        
        return True

    @api.multi
    def action_account_approve(self):
        return super(SaleOrder, self).action_confirm()

    @api.multi
    def action_account_disapprove(self):
        self.filtered(lambda s: s.state == 'account_review').write({'state': 'draft'})
        return True
