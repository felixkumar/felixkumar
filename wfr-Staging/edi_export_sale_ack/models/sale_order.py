import datetime
import logging

EDI_DATE_FORMAT = '%Y-%m-%d'

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_name = fields.Char(string='Partner Name', related='partner_id.name')
    partner_phone = fields.Char(string='Partner Phone', related='partner_id.phone')
    partner_email = fields.Char(string='Partner Email', related='partner_id.email')
    trading_partnerid = fields.Char(string='Trading Partner ID', related='partner_id.trading_partnerid')
    edi_terms_type = fields.Char(string='EDI Terms Type', compute='_compute_edi_terms_values')
    edi_terms_basis_date_code = fields.Char(string='EDI Terms Basis Date Code', compute='_compute_edi_terms_values')
    edi_terms_discount_percentage = fields.Char(string='EDI Terms Discount Percentage', compute='_compute_edi_terms_values')
    edi_terms_discount_date = fields.Char(string='EDI Terms Discount Date', compute='_compute_edi_terms_values')
    edi_terms_discount_due_days = fields.Char(string='EDI Terms Discount Due Days', compute='_compute_edi_terms_values')
    edi_terms_net_due_date = fields.Char(string='EDI Terms Net Due Date', compute='_compute_edi_terms_values')
    edi_terms_net_due_days = fields.Char(string='EDI Terms Discount Date', compute='_compute_edi_terms_values')
    edi_terms_description = fields.Char(string='EDI Terms Description', compute='_compute_edi_terms_values')
    edi_fob_pay_code = fields.Char(string='EDI FOB Pay Code', compute='_compute_edi_terms_values')
    edi_fob_location_qualifier = fields.Char(string='EDI FOB Location Qualifier', compute='_compute_edi_terms_values')
    edi_fob_location_description = fields.Char(string='EDI FOB Location Description', compute='_compute_edi_terms_values')
    edi_fob_transportation_terms_type = fields.Char(string='EDI FOB Transportaion Terms Type', compute='_compute_edi_terms_values')
    edi_fob_transportation_terms = fields.Char(string='EDI FOB Transportation Terms', compute='_compute_edi_terms_values')

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        base_edi = self.env['edi.sync.action']
        for order in self:
            if order.partner_id.send_edi_order_ack:
                sync_action = base_edi.search([('doc_type_id.doc_code', '=', 'export_sale_acknowledgement_xml')])
                if sync_action:
                    base_edi._do_doc_sync_cron(sync_action_id=sync_action, records=self)
        return res

    @api.depends('edi_customer_payment_terms')
    def _compute_edi_terms_values(self):
        for order in self:
            text_payment_terms = order.edi_customer_payment_terms
            terms_dict = {key.strip():value.strip() for line in text_payment_terms.split('\n') if line for term in line.split(',') for key, value in [term.split(':')]} if text_payment_terms else {}

            today_date = datetime.datetime.now()

            order.edi_terms_type = terms_dict.get('Terms Type', '')
            order.edi_terms_basis_date_code = terms_dict.get('Basis Date Code', '')
            order.edi_terms_discount_percentage = terms_dict.get('Discount Percentage', '')
            order.edi_terms_discount_date = terms_dict.get('Discount Date', today_date)
            order.edi_terms_discount_due_days = terms_dict.get('edi_terms_discount_due_days', '')
            order.edi_terms_net_due_date = terms_dict.get('Net Due Date', '')
            order.edi_terms_net_due_days = terms_dict.get('Net Due Days', '')
            order.edi_terms_description = terms_dict.get('Terms Description', '')
            order.edi_fob_pay_code = terms_dict.get('Terms Description', '')
            order.edi_fob_location_qualifier = terms_dict.get('FOB Location Qualifier', '')
            order.edi_fob_location_description = terms_dict.get('FOB Location Description', '')
            order.edi_fob_transportation_terms_type = terms_dict.get('Transportation Terms Type', '')
            order.edi_fob_transportation_terms = terms_dict.get('Transportation Terms', '')


    def _get_edi_partner(self):
        self.ensure_one()
        return self.partner_id


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    edi_gtin = fields.Char(related='product_id.edi_gtin')
    edi_product_uom_code = fields.Char(related='product_uom.edi_code')
    edi_date_time_qualifier = fields.Char(related='order_id.edi_date_time_qualifier')
    edi_product_characteristic_code = fields.Char(related='product_id.edi_product_characteristic_code')
    edi_note_code = fields.Selection(related='order_id.edi_note_code')
    edi_note = fields.Html(related='order_id.note')
