# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from pytz import timezone, utc

from odoo import api, fields, models
from odoo.http import request


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _is_invalid_renting_dates(self, company, start_date=None, end_date=None):
        """ Check the pickup and return dates are invalid
        """
        days_forbidden = company._get_renting_forbidden_days()
        info = self._get_renting_dates_info(
            start_date or self.start_date, end_date or self.return_date, company
        )
        return (
            # 15 minutes of allowed time between adding the product to cart and paying it.
            (self.start_date or start_date) < fields.Datetime.now() - timedelta(minutes=15)
            or info['pickup_day'] in days_forbidden
            or info['return_day'] in days_forbidden
            or info['duration'] < company.renting_minimal_time_duration
        )

    @api.model
    def _get_renting_dates_info(self, start_date, end_date, company):
        """ Get renting dates basic information in order to validates the days and duration
            :param start_date: naive datetime object which is the start date in UTC
            :param end_date: naive datetime object which is the end date in UTC
        Note: api.model
        """
        client_tz = timezone(self._get_tz())
        start_date = utc.localize(start_date).astimezone(client_tz)
        end_date = utc.localize(end_date).astimezone(client_tz)
        duration_vals = self.env['product.pricing']._compute_duration_vals(start_date, end_date)
        return {
            'pickup_day': start_date.isoweekday(),
            'return_day': end_date.isoweekday(),
            'duration': duration_vals[company.renting_minimal_time_unit],
        }

    def _get_tz(self):
        return request and request.httprequest.cookies.get('tz') or super()._get_tz()

    def _is_reorder_allowed(self):
        if self.temporal_type == 'rental':
            return False
        return super(SaleOrderLine, self)._is_reorder_allowed()
