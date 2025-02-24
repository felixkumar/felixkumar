# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.sql import column_exists, create_column


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # l10n_de_datev_identifier now only targets vendors instead of all partners
    l10n_de_datev_identifier = fields.Integer(
        string='DateV Vendor',
        help="In the DateV export of the General Ledger, each vendor will be identified by this identifier. "
        "If this identifier is not set, the database id of the partner will be added to a multiple of ten starting by the number 7."
        "The account code's length can be specified in the company settings."
    )
    l10n_de_datev_identifier_customer = fields.Integer(
        string='DateV Customer',
        copy=False,
        tracking=True,
        index='btree_not_null',
        compute="_compute_l10n_de_datev_identifier_customer", store=True, readonly=False,
        help="In the DateV export of the General Ledger, each customer will be identified by this identifier. "
        "If this identifier is not set, the database id of the partner will be added to a multiple of ten starting by the number 1."
        "The account code's length can be specified in the company settings."
    )

    def _auto_init(self):
        cr = self.env.cr
        if not column_exists(cr, "res_partner", "l10n_de_datev_identifier_customer") and column_exists(cr, "res_partner", "l10n_de_datev_identifier"):
            create_column(cr, "res_partner", "l10n_de_datev_identifier_customer", "int4")
            cr.execute("UPDATE res_partner SET l10n_de_datev_identifier_customer = l10n_de_datev_identifier")
        return super()._auto_init()

    @api.constrains('l10n_de_datev_identifier_customer')
    def _check_datev_identifier_customer(self):
        self.flush_model(['l10n_de_datev_identifier_customer'])
        self.env.cr.execute("""
            SELECT 1 FROM res_partner
            WHERE l10n_de_datev_identifier_customer != 0
            GROUP BY l10n_de_datev_identifier_customer
            HAVING COUNT(*) > 1
        """)

        if self.env.cr.dictfetchone():
            raise ValidationError(_('You have already defined a partner with the same Datev Customer identifier'))

    def _compute_l10n_de_datev_identifier_customer(self):
        # Compute without depends so it is only computed when installing the module
        for partner in self:
            partner.l10n_de_datev_identifier_customer = partner.l10n_de_datev_identifier
