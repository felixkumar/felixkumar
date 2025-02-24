from odoo import api, fields, models
import lxml.etree as etree


class AccountPaymentTerm(models.Model):
    _name = 'account.payment.term'
    _inherit = ['account.payment.term', 'edi.import.tools.mixin']

    @api.model
    def get_payment_terms(self, payment_terms_node, additional_fields, nsmap=None):
        payment_terms_dict = {etree.QName(child).localname: child.text for child in payment_terms_node.getchildren()}
        terms_type = payment_terms_dict.get('TermsType', '')
        discount_percentage = payment_terms_dict.get('TermsDiscountPercentage', '')
        discount_due_days = payment_terms_dict.get('TermsDiscountDueDays', '')
        net_due_days = payment_terms_dict.get('TermsNetDueDays', '')
        terms_description = payment_terms_dict.get('TermsDescription', '')

        payment_term_id = False
        payment_term_line_id = self.env['account.payment.term.line'].search(
            [('discount_percentage', '=', discount_percentage), ('discount_days', '=', discount_due_days),
             ('days', '=', net_due_days)], limit=1)
        if payment_term_line_id:
            return payment_term_line_id.payment_id.id

        if terms_description:
            payment_term_id = self.env['account.payment.term'].search([('edi_description', '=', terms_description)], limit=1)

        if not payment_term_id:
            # Immediate Payment
            if terms_type == '08':
                payment_term_id = self.env['account.payment.term'].search([]) \
                    .filtered(lambda p: p.line_ids.filtered(lambda line: line.value == 'balance' and line.days == 0))

            if terms_type == '10' and not payment_term_id:
                payment_term_id = self.env['account.payment.term'].search([]) \
                    .filtered(lambda p: p.line_ids.filtered(lambda line: line.value == 'balance' and line.days == 0))

            elif discount_percentage and not payment_term_id:
                # Retrieve the Odoo payment term record which lines match the EDI discount and the days
                payment_term_id = self.env['account.payment.term'].search([]) \
                    .filtered(
                    lambda p: p.line_ids.filtered(
                        lambda line: line.value == 'percent' and line.days == int(
                            discount_due_days)) and p.line_ids.filtered(
                        lambda line: line.value == 'balance' and line.days == int(net_due_days or discount_due_days)))
            elif net_due_days and not payment_term_id:
                payment_term_id = self.env['account.payment.term'].search([]) \
                    .filtered(
                    lambda p: not p.line_ids.filtered(lambda line: line.value == 'percent') and p.line_ids.filtered(
                        lambda line: line.value == 'balance' and line.days == int(net_due_days)))

        return payment_term_id[:1].id
