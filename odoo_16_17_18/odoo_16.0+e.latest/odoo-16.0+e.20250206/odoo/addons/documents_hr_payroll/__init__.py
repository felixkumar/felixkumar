# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import controllers
from . import models


from odoo import api, SUPERUSER_ID


def _generate_payroll_document_folders(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['res.company'].search([])._generate_payroll_document_folders()
