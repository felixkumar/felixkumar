#coding: utf-8

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class custom_dummy_type(models.Model):
    """
    The model to introduce "dummy" type to use instead of type for resource type and services
    """
    _name = "custom.dummy.type"
    _description = "Dummy Type Model"

    name = fields.Char()
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """
        Overwrite to make sure always empty list is returned
        """
        return []
