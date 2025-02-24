# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tests import HttpCase, tagged
from odoo.addons.mail.tests.common import mail_new_test_user


@tagged('-at_install', 'post_install')
class ProjectEnterpriseTestUi(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_groups = 'base.group_user,project.group_project_manager'
        if 'account.move.line' in cls.env:
            user_groups += ',account.group_account_invoice'
        cls.user_project_manager = mail_new_test_user(
            cls.env,
            company_id=cls.env.company.id,
            email='gilbert.testuser@test.example.com',
            login='user_project_manager',
            groups=user_groups,
            name='Gilbert ProjectManager',
            tz='Europe/Brussels',
        )

    def test_01_ui(self):
        self.env['project.task'].create({
            'name': 'Yolo Task',
            'project_id': self.env['project.project'].create({'name': 'Yolo Project'}).id,
            'user_ids': [(4, self.user_project_manager.id)],
            'planned_date_begin': datetime.now() + relativedelta(day=1, hour=6, minute=0, second=0),
            'planned_date_end': datetime.now() + relativedelta(day=7, hour=18, minute=0, second=0),
        })
        self.start_tour("/", 'project_enterprise_tour', login='user_project_manager')
