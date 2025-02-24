# -*- coding: utf-8 -*-

def post_init_hook(cr, registry):
    """
    The goal is to make sure website.business.order receive required fields
    """
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    custom_fields_objects = env["custom.appointment.contact.info.field"].search([
        "|",
            ("active", "=", True),
            ("active", "=", False),
    ])
    custom_fields_objects.write({})

