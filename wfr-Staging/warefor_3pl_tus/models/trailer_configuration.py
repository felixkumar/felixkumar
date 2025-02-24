# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class TrailerConfiguration(models.Model):
    _name = 'trailer.configuration'
    _description = 'Trailer configuration'

    name = fields.Char(_("name"))
    trailer_size = fields.Float(_("Trailer Size"))
    cu_ft = fields.Float(_("Cu Ft"))
    pay_load_lbs = fields.Float(_("Pay Load (Lbs)"))
    cu_metric = fields.Float(_("Cubic Metric"))
    pay_load_kg = fields.Float(_("Pay Load (Kg)"))
    description = fields.Text(string="Description")

    @api.onchange('cu_ft')
    def onchange_cu_ft(self):
        """
        Converting foot to metric
        """
        for rec in self:
            if rec.cu_ft:
                    rec.cu_metric = round(rec.cu_ft * 0.0283168, 3)

    @api.onchange('pay_load_lbs')
    def onchange_pay_load_lbs(self):
        """"
        Converting Pound to Kg weight
        """
        for rec in self:
            if rec.pay_load_lbs:
                rec.pay_load_kg = round(rec.pay_load_lbs * 0.453592, 3)
