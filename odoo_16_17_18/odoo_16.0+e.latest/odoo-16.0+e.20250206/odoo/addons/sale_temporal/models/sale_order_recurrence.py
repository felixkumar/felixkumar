# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, _lt
from odoo.tools import get_timedelta
from odoo.tools import float_compare, float_is_zero


class SaleOrderRecurrence(models.Model):
    _name = 'sale.temporal.recurrence'
    _description = 'Sale temporal Recurrence'
    _order = 'unit,duration'

    active = fields.Boolean(default=True)
    name = fields.Char(compute='_compute_name', store=True, readonly=False)
    duration = fields.Integer(string="Duration", required=True, default=1,
                              help="Minimum duration before this rule is applied. If set to 0, it represents a fixed temporal price.")
    unit = fields.Selection([('day', 'Days'), ("week", "Weeks"), ("month", "Months"), ('year', 'Years')],
        string="Unit", required=True, default='month')
    duration_display = fields.Char(compute='_compute_duration_display')
    subscription_unit_display = fields.Char(compute='_compute_subscription_unit_display')

    _sql_constraints = [
        ('temporal_recurrence_duration', "CHECK(duration >= 0)", "The pricing duration has to be greater or equal to 0."),
    ]

    @api.depends('duration', 'unit')
    def _compute_name(self):
        for record in self:
            if not record.name:
                record.name = _("%s %s", record.duration, record.unit)

    def get_recurrence_timedelta(self):
        self.ensure_one()
        return get_timedelta(self.duration, self.unit)

    @api.depends('duration', 'unit')
    def _compute_duration_display(self):
        for record in self:
            record.duration_display = "%s %s" % (
                record.duration, record._get_unit_label(record.duration)
            )

    def _get_unit_label(self, duration):
        """ Get the translated product pricing unit label. """
        if duration is None:
            return ""
        self.ensure_one()
        if float_compare(duration, 1.0, precision_digits=2) < 1\
           and not float_is_zero(duration, precision_digits=2):
            singular_labels = {
                'hour': _lt("Hour"),
                'day': _lt("Day"),
                'week': _lt("Week"),
                'month': _lt("Month"),
                'year': _lt("Year"),
            }
            if self.unit in singular_labels:
                return str(singular_labels[self.unit])
        return dict(
            self._fields['unit']._description_selection(self.env)
        )[self.unit]

    @api.depends('duration', 'unit')
    def _compute_subscription_unit_display(self):
        for order in self:
            if order.unit == 'week':
                order.subscription_unit_display = _('per %s weeks', order.duration) if order.duration > 1 else _('per week')
            elif order.unit == 'month':
                order.subscription_unit_display = _('per %s months', order.duration) if order.duration > 1 else _('per month')
            elif order.unit == 'year':
                order.subscription_unit_display = _('per %s years', order.duration) if order.duration > 1 else _('per year')
            else:
                order.subscription_unit_display = _('This recurrence unit is not supported.')
