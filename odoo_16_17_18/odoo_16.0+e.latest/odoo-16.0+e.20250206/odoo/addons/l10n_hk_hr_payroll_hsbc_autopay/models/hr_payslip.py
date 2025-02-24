# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from odoo import fields, models, _
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    hsbc_export = fields.Binary(string='HSBC Autopay File', readonly=True)
    hsbc_export_date = fields.Datetime(string='HSBC Generation Date')
    hsbc_export_filename = fields.Char(string='Autopay File Name')

    def _generate_h2h_autopay(self, header_data: dict):
        header = (
            f'H{header_data["digital_pic_id"]:<11}HKMFPS02{"":<3}'
            f'{header_data["customer_ref"]:<35}{header_data["payment_date"]:%Y/%m/%d%H:%M:%S}'
            f'{"":<1}{header_data["authorisation_type"]}{"":<2}PH{"":<79}\n'
        )
        return header

    def _generate_hsbc_autopay(self, header_data: dict, payments_data: dict):
        header = (
            f'PHF{header_data["payment_set_code"]}{header_data["ref"]:<12}{header_data["payment_date"]:%Y%m%d}'
            f'{header_data["autopay_partner_bank_id"].acc_number + "SA" + header_data["currency"]:<35}'
            f'{header_data["currency"]}{header_data["payslips_count"]:07}{int(header_data["amount_total"] * 100):017}'
            f'{"":<1}{"":<311}\n'
        )
        datas = []
        for payment in payments_data:
            datas.append(
                f'PD{payment["bank_code"]:<3}{payment["type"].upper()}{payment["autopay_field"]:<34}'
                f'{int(payment["amount"] * 100):017}{payment["identifier"]:<35}{payment["ref"]:<35}'
                f'{payment["bank_account_name"]:<140}{"":<130}'
            )
        data = '\n'.join(datas)
        return header + data

    def _create_apc_file(self, payment_set_code: str, batch_type: str = 'first', ref: str = None, file_name: str = None, **kwargs):
        invalid_payslips = self.filtered(lambda p: p.currency_id.name not in ['HKD', 'CNY'])
        if invalid_payslips:
            raise UserError(_("Only accept HKD or CNY currency.\nInvalid currency for the following payslips:\n%s", '\n'.join(invalid_payslips.mapped('name'))))
        companies = self.mapped('company_id')
        if len(companies) > 1:
            raise UserError(_("Only support generating the HSBC autopay report for one company."))
        currencies = self.mapped('currency_id')
        if len(currencies) > 1:
            raise UserError(_("Only support generating the HSBC autopay report for one currency"))
        invalid_employees = self.mapped('employee_id').filtered(lambda e: not e.bank_account_id)
        if invalid_employees:
            raise UserError(_("Some employees (%s) don't have a bank account.", ','.join(invalid_employees.mapped('name'))))
        invalid_employees = self.mapped('employee_id').filtered(lambda e: not e.l10n_hk_autopay_account_type)
        if invalid_employees:
            raise UserError(_("Some employees (%s) haven't set the autopay type.", ','.join(invalid_employees.mapped('name'))))
        invalid_banks = self.employee_id.bank_account_id.mapped('bank_id').filtered(lambda b: not b.l10n_hk_bank_code)
        if invalid_banks:
            raise UserError(_("Some banks (%s) don't have a bank code", ','.join(invalid_banks.mapped('name'))))
        invalid_bank_accounts = self.mapped('employee_id').filtered(
            lambda e: e.l10n_hk_autopay_account_type in ['bban', 'hkid'] and not e.bank_account_id.acc_holder_name)
        if invalid_bank_accounts:
            raise UserError(_("Some bank accounts (%s) don't have a bank account name.", ','.join(invalid_bank_accounts.mapped('bank_account_id.acc_number'))))
        rule_code = {'first': 'MEA', 'second': 'SBA'}[batch_type]
        payslips = self.filtered(lambda p: p.struct_id.code == 'CAP57MONTHLY' and p.line_ids.filtered(lambda line: line.code == rule_code))
        if not payslips:
            raise UserError(_("No payslip to generate the HSBC autopay report."))

        payment_date = fields.Datetime.now()
        autopay_type = self.company_id.l10n_hk_autopay_type
        if autopay_type == 'h2h':
            h2h_header_data = {
                'authorisation_type': kwargs.get('authorisation_type'),
                'customer_ref': kwargs.get('customer_ref', ''),
                'digital_pic_id': kwargs.get('digital_pic_id'),
                'payment_date': payment_date,
            }

        header_data = {
            'ref': ref,
            'currency': payslips.currency_id.name,
            'amount_total': sum(payslips.line_ids.filtered(lambda line: line.code == rule_code).mapped('amount')),
            'payment_date': payment_date,
            'payslips_count': len(payslips),
            'payment_set_code': payment_set_code,
            'autopay_partner_bank_id': payslips.company_id.l10n_hk_autopay_partner_bank_id,
        }

        payments_data = []
        for payslip in payslips:
            payments_data.append({
                'id': payslip.id,
                'ref': payslip.employee_id.l10n_hk_autopay_ref or '',
                'type': payslip.employee_id.l10n_hk_autopay_account_type,
                'amount': sum(payslip.line_ids.filtered(lambda line: line.code == rule_code).mapped('amount')),
                'identifier': payslip.employee_id.l10n_hk_autopay_identifier or '',
                'bank_code': payslip.employee_id.get_l10n_hk_autopay_bank_code(),
                'autopay_field': payslip.employee_id.get_l10n_hk_autopay_field(),
                'bank_account_name': payslip.employee_id.bank_account_id.acc_holder_name or '',
            })

        apc_doc = payslips._generate_hsbc_autopay(header_data, payments_data)
        if autopay_type == 'h2h':
            apc_doc = payslips._generate_h2h_autopay(h2h_header_data) + apc_doc
        apc_binary = base64.encodebytes(apc_doc.encode('ascii'))

        file_name = file_name and file_name.replace('.apc', '')
        if batch_type == 'first':
            payslips.mapped('payslip_run_id').write({
                'l10n_hk_autopay_export_first_batch_date': payment_date,
                'l10n_hk_autopay_export_first_batch': apc_binary,
                'l10n_hk_autopay_export_first_batch_filename': (file_name or 'HSBC_Autopay_export_first_batch') + '.apc',
            })
        else:
            payslips.mapped('payslip_run_id').write({
                'l10n_hk_autopay_export_second_batch_date': payment_date,
                'l10n_hk_autopay_export_second_batch': apc_binary,
                'l10n_hk_autopay_export_second_batch_filename': (file_name or 'HSBC_Autopay_export_second_batch') + '.apc',
            })
