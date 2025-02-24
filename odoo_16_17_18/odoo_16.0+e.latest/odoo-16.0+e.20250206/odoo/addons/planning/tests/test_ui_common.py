# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import HttpCase


class TestUiCommon(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['hr.employee'].create({
            'name': 'Thibault',
            'work_email': 'thibault@a.be',
            'tz': 'UTC',
            'employee_type': 'freelance',
            'flexible_hours': True,
        })
