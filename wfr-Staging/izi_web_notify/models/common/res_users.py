# -*- coding: utf-8 -*-
# Copyright 2023 IZI PT Solusi Usaha Mudah

from odoo import _, api, exceptions, fields, models

import logging
_logger = logging.getLogger(__name__)

DEFAULT_MESSAGE = "Default message"

SUCCESS = "success"
DANGER = "danger"
WARNING = "warning"
INFO = "info"
DEFAULT = "default"


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.depends("create_date")
    def _compute_channel_names(self):
        for record in self:
            res_id = record.id
            record.izi_notification_channel_name = "izi_notify_channel_%s" % res_id

    izi_notification_channel_name = fields.Char(compute="_compute_channel_names")

    def _notify_channel(
        self, type_message=DEFAULT, message=DEFAULT_MESSAGE, title=None, sticky=False
    ):
        
        # pylint: disable=protected-access
        if not self.env.user._is_admin() and any(
            user.id != self.env.uid for user in self
        ):
            raise exceptions.UserError(
                _("Could not send a notification to another user!.")
            )
        # channel_id = "notify_{}_channel_name".format(type_message)
        channel_name_field = "izi_notification_channel_name"
        param_message = {
            "type": type_message,
            "message": message,
            "title": title,
            "sticky": sticky,
        }
        notifications = [(record[channel_name_field], param_message) for record in self]
        
        self.env["bus.bus"].sendmany(notifications)
