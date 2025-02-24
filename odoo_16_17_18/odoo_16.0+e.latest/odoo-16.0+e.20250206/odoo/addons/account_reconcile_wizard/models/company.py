from odoo import _, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_violated_lock_dates(self, accounting_date, has_tax):
        """Get all the lock dates affecting the current accounting_date.
        :param accoutiaccounting_dateng_date: The accounting date
        :param has_tax: If any taxes are involved in the lines of the invoice
        :return: a list of tuples containing the lock dates ordered chronologically.
        """
        self.ensure_one()
        locks = []
        user_lock_date = self._get_user_fiscal_lock_date()
        if accounting_date and user_lock_date and accounting_date <= user_lock_date:
            locks.append((user_lock_date, _('user')))
        tax_lock_date = self.tax_lock_date
        if accounting_date and tax_lock_date and has_tax and accounting_date <= tax_lock_date:
            locks.append((tax_lock_date, _('tax')))
        locks.sort()
        return locks
