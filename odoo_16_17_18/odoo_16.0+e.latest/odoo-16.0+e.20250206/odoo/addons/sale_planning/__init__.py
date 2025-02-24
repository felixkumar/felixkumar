# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import controllers
from . import models
from . import report

def uninstall_hook(cr, registry):
    # remove plannings which are not scheduled
    cr.execute("DELETE FROM planning_slot WHERE start_datetime is null OR end_datetime is null")
    # restore required
    cr.execute("""
        ALTER TABLE planning_slot
            ALTER COLUMN start_datetime SET NOT NULL,
            ALTER COLUMN end_datetime SET NOT NULL
    """)
