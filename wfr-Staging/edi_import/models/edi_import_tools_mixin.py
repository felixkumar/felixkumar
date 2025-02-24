from datetime import datetime

import pytz

from odoo import api, models


class EdiImportMixin(models.AbstractModel):
    _name = 'edi.import.tools.mixin'
    _description = 'Mixin providing useful edi import tools'

    @api.model
    def default_text(self, node, default=''):
        return node.text if node is not None else default

    @api.model
    def convert_TZ_UTC(self, TZ_datetime, is_datetime=False):
        """Convert datetime from user timezone to UTZ"""
        tz = pytz.timezone(self.env.user.tz or str(pytz.utc))
        format = "%Y-%m-%d %H:%M:%S"
        local_datetime_format = "%Y-%m-%d"
        now_utc = datetime.utcnow()  # Current time in UTC
        now_timezone = now_utc.astimezone(tz)  # Convert to current user time zone
        UTC_OFFSET_TIMEDELTA = datetime.strptime(now_utc.strftime(format), format) - datetime.strptime(now_timezone.strftime(format), format)
        if is_datetime:
            local_datetime_format = format
        local_datetime = datetime.strptime(TZ_datetime, local_datetime_format)
        result_utc_datetime = local_datetime + UTC_OFFSET_TIMEDELTA
        return result_utc_datetime.strftime(format)
