# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import single_email_re


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Autopay fields
    l10n_hk_autopay_account_type = fields.Selection(
        selection=[
            ('bban', 'BBAN'),
            ('svid', 'SVID'),
            ('emal', 'EMAL'),
            ('mobn', 'MOBN'),
            ('hkid', 'HKID')
        ],
        default='bban',
        string='Autopay Type',
        groups='hr.group_hr_user'
    )
    l10n_hk_autopay_svid = fields.Char(string='FPS Identifier', groups="hr.group_hr_user")
    l10n_hk_autopay_emal = fields.Char(string='Autopay Email Address', groups="hr.group_hr_user")
    l10n_hk_autopay_mobn = fields.Char(string='Autopay Mobile Number', groups="hr.group_hr_user")
    l10n_hk_autopay_identifier = fields.Char(string='Autopay Identifier', groups="hr.group_hr_user")
    l10n_hk_autopay_ref = fields.Char(string='Autopay Reference', groups="hr.group_hr_user")

    @api.constrains('l10n_hk_autopay_emal')
    def _check_l10n_hk_autopay_emal(self):
        for employee in self:
            if employee.l10n_hk_autopay_emal and not single_email_re.match(employee.l10n_hk_autopay_emal):
                raise ValidationError(_('Invalid Email! Please enter a valid email address.'))

    @api.constrains('l10n_hk_autopay_mobn')
    def _check_l10n_hk_auto_mobn(self):
        auto_mobn_re = re.compile(r"^[+]\d{1,3}-\d{6,12}$")
        for employee in self:
            if employee.l10n_hk_autopay_mobn and not auto_mobn_re.match(employee.l10n_hk_autopay_mobn):
                raise ValidationError(_('Invalid Mobile! Please enter a valid mobile number.'))

    def get_l10n_hk_autopay_bank_code(self):
        self.ensure_one()
        if self.l10n_hk_autopay_account_type == 'bban':
            return self.bank_account_id.bank_id.l10n_hk_bank_code
        else:
            return ''

    def get_l10n_hk_autopay_field(self):
        self.ensure_one()
        if self.l10n_hk_autopay_account_type == 'bban':
            return self.bank_account_id.acc_number
        if self.l10n_hk_autopay_account_type == 'svid':
            return self.l10n_hk_autopay_svid
        if self.l10n_hk_autopay_account_type == 'emal':
            return self.l10n_hk_autopay_emal
        if self.l10n_hk_autopay_account_type == 'mobn':
            return self.l10n_hk_autopay_mobn
        if self.l10n_hk_autopay_account_type == 'hkid':
            return self.identification_id
