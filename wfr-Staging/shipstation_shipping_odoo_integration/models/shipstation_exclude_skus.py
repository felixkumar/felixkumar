# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ShipstationExcludeSkus(models.Model):
    """
    Model to manage SKUs that should be excluded from Shipstation processing.
    """
    _name = 'shipstation.exclude.skus'
    _description = 'Shipstation Exclude SKUs'
    _rec_name = 'key'
    _order = 'key'
    _allow_sudo_commands = False

    # Fields to store SKU key and value
    key = fields.Char(required=True)
    value = fields.Text(required=True)

    # Ensure each key is unique
    _sql_constraints = [
        ('key_uniq', 'unique (key)', 'Key must be unique.')
    ]

    @api.model
    def get_param(self, key, default=False):
        """
        Retrieve the value for a given key.

        :param string key: The key of the parameter value to retrieve.
        :param string default: Default value if parameter is missing.
        :return: The value of the parameter, or `default` if it does not exist.
        :rtype: string
        """
        self.check_access_rights('read')  # Ensure read access rights
        return self._get_param(key) or default

    @api.model
    def _get_param(self, key):
        """
        Internal method to retrieve the value for a given key directly from the database.

        :param string key: The key of the parameter value to retrieve.
        :return: The value of the parameter, or None if it does not exist.
        :rtype: string
        """
        # Bypass ORM to ensure it works even when ORM is not fully ready
        self.flush_model(['key', 'value'])
        self.env.cr.execute("SELECT value FROM shipstation_exclude_skus WHERE key = %s", [key])
        result = self.env.cr.fetchone()
        return result and result[0]