from odoo import models, Command


class FreightFreightInherit(models.Model):
    _inherit = 'freight.freight'

    def action_create_credit_memo(self):
        billing_dict = {}
        partner = self[0].partner_id
        for rec in self:
            lines = rec.vas_cost_ids
            for line in lines:
                if (line.product_id, line.unit_price) in billing_dict:
                    billing_dict[(line.product_id, line.unit_price)]['qty'] += line.total_unit
                else:
                    billing_dict[(line.product_id, line.unit_price)] = {'name': line.product_id,
                                                                        'unit_price': line.unit_price,
                                                                        'qty': line.total_unit}
        credit_inv_lines = [Command.create({"product_id": x['name'].id,
                                            "price_unit": x['unit_price'],
                                            "quantity": x['qty']}) for x in billing_dict.values()]
        credit_vals = {
            "partner_id": partner.id,
            "move_type": "out_refund",
            "invoice_line_ids": credit_inv_lines,
            "edi_purchase_order": ', '.join(rec.customer_po for rec in self if rec.customer_po)
        }
        credit_rec = self.env['account.move'].create(credit_vals)
        for record in self:
            record.write({
                "account_move_ids": [Command.link(credit_rec.id)]
            })

        action = credit_rec.action_open_business_doc()
        return action
