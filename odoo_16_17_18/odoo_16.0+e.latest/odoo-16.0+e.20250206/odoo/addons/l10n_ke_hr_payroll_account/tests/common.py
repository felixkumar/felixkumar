# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestL10nKeHrPayrollBase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # make the company
        cls.ke_company = cls.env['res.company'].create({
            'name': 'Test Company',
            'country_id': cls.env.ref('base.ke').id,
        })

        # setup the environment
        cls.env.user.company_ids |= cls.ke_company
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=cls.ke_company.ids))

        # creating 2 employees and their contracts with the minimum infos required
        # create the employee 1 and his contract
        cls.employee_ke_1 = cls.env['hr.employee'].create({
            'name': 'Test Employee 1',
            'company_id': cls.ke_company.id,
        })
        cls.employee_ke_1_contract = cls.env['hr.contract'].create({
            'name': 'Test Contract KE 1',
            'employee_id': cls.employee_ke_1.id,
            'wage': 24000.0,
            'company_id': cls.ke_company.id,
            'state': 'open',
            'date_start': '2020-01-01',
        })
        cls.employee_ke_1.write({'contract_id': cls.employee_ke_1_contract.id})

        # create the employee 2 and his contract
        cls.employee_ke_2 = cls.env['hr.employee'].create({
            'name': 'Test Employee 2',
            'company_id': cls.ke_company.id,
        })
        cls.employee_ke_2_contract = cls.env['hr.contract'].create({
            'name': 'Test Contract KE 2',
            'employee_id': cls.employee_ke_2.id,
            'wage': 75000.0,
            'company_id': cls.ke_company.id,
            'state': 'open',
            'date_start': '2020-01-01',
        })
        cls.employee_ke_2.write({'contract_id': cls.employee_ke_2_contract.id})

        # create the poorest employee possible
        cls.employee_zero_wage = cls.env['hr.employee'].create({
            'name': 'Test Employee 0 Wage',
            'company_id': cls.ke_company.id,
        })

        cls.employee_zero_wage_contract = cls.env['hr.contract'].create({
            'name': 'Test Contract KE 0 Wage',
            'employee_id': cls.employee_zero_wage.id,
            'wage': 0.0,
            'company_id': cls.ke_company.id,
            'state': 'open',
            'date_start': '2020-01-01',
        })
