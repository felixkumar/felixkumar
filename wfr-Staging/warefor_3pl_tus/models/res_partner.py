# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    nda = fields.Binary(string="NDA", tracking=True)
    ach_auth = fields.Binary(string="ACH Auth", tracking=True)
    w9 = fields.Binary(string="W9", tracking=True)
    # other_file = fields.Binary(string="Others")
    other_file = fields.Many2many('ir.attachment', string='Others', tracking=True)
    vendor_identifier = fields.Char("Vendor Identifier")
    warefor_vendor_number = fields.Char("Warefor Vendor Number")
    vendor_code_ids = fields.One2many('vendor.code.line', 'partner_id', string="Vendor Code")
    require_1099 = fields.Boolean(string="Require 1099")

    company_banking_info = fields.Text(string="Company Banking Info", company_dependent=True)
    tax_classification_id = fields.Many2one(comodel_name="tax.classification", string="Tax Classification", )
    default_invoice_text = fields.Char(string="Invoice Note")
    freight_customer_id = fields.Many2one(comodel_name="res.partner", string="Customer/Consignee")
    use_virtual_location = fields.Boolean(compute="_compute_virtual_location_", string="Use Virtual Inventory?")
    virtual_location_id = fields.Many2one(comodel_name='stock.location', string="Virtual Location",
                                          domain="[('usage','=','transit')]")
    dba_id = fields.Many2one("vendor.dba", string="DBA")
    is_auto_payment_method = fields.Boolean(string="Auto Payment Method")
    is_online_payment_method = fields.Boolean(string="Online Payment Method")
    is_oxford_usa_corporation = fields.Boolean(string="Is Oxford USA Corporation")

    @api.onchange('is_auto_payment_method')
    def onchange_is_auto_payment_method(self):
        if self.is_auto_payment_method:
            self.is_auto_payment_method = True
            self.is_online_payment_method = False
    @api.onchange('is_online_payment_method')
    def onchange_is_online_payment_method(self):
        if self.is_online_payment_method:
            self.is_online_payment_method = True
            self.is_auto_payment_method = False

    @api.depends_context('company')
    def _compute_virtual_location_(self):
        company = self.env.company
        for rec in self:
            rec.use_virtual_location = company and company.use_virtual_location or False

    def _get_name(self):
        """ Utility method to allow name_get to be overrided without re-browse the partner """
        partner = self
        name = partner.name or ''

        if partner.company_name or partner.parent_id:
            if not name and partner.type in ['invoice', 'delivery', 'other']:
                name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
            if not partner.is_company:
                name = self._get_contact_name(partner, name)
        if self._context.get('show_dba') and self._context.get('res_partner_search_mode') == 'supplier':
            name = "%s \n %s" % (name, partner.dba_id and partner.dba_id.name or '')
        if self._context.get('show_address_only'):
            name = partner._display_address(without_company=True)
        if self._context.get('show_address'):
            name = name + "\n" + partner._display_address(without_company=True)
        name = re.sub(r'\s+\n', '\n', name)
        if self._context.get('partner_show_db_id'):
            name = "%s (%s)" % (name, partner.id)
        if self._context.get('address_inline'):
            splitted_names = name.split("\n")
            name = ", ".join([n for n in splitted_names if n.strip()])
        if self._context.get('show_email') and partner.email:
            name = "%s <%s>" % (name, partner.email)
        if self._context.get('html_format'):
            name = name.replace('\n', '<br/>')
        if self._context.get('show_vat') and partner.vat:
            name = "%s ‒ %s" % (name, partner.vat)
        return name.strip()


class VendorCodeLine(models.Model):
    _name = "vendor.code.line"
    _description = 'Vendor Code Line'
    _rec_name = 'code'

    code = fields.Char(string="Code")
    customer_id = fields.Many2one(comodel_name="res.partner", string="Customer")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer")


class TaxClassification(models.Model):
    _name = "tax.classification"
    _description = 'Tax Classification'

    name = fields.Char(string='Name')
    active = fields.Boolean(_('Active'), default=True)
