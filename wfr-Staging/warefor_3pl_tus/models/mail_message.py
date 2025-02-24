# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, _, api


class MailMessage(models.Model):
    _inherit = "mail.message"

    def write(self, vals):
        return super(MailMessage, self.sudo()).write(vals)
