# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_mod_boe_sequence(self, mod_version):
        """ Get or create mod BOE sequence for the current company

        :param str mod_version: any of "347" or "349"
        :return: the sequence record
        """
        self.ensure_one()
        assert mod_version in ("347", "349")
        mod_sequence_code = 'l10n_es.boe.mod_%s' % mod_version
        mod_sequence = self.env['ir.sequence'].search([
            ('company_id', '=', self.id), ('code', '=', mod_sequence_code),
        ])
        if not mod_sequence:
            mod_sequence = self.env["ir.sequence"].create({
                'name': "Mod %s BOE sequence for company %s" % (mod_version, self.name),
                'code': mod_sequence_code,
                'padding': 10,
                'company_id': self.id,
            })
        return mod_sequence[0]
