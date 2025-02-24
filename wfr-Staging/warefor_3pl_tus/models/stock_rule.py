# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from collections import defaultdict

from odoo import SUPERUSER_ID, _, api, fields, models, registry
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, html_escape

from odoo.addons.stock.models.stock_rule import ProcurementException

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move, ... """
    _inherit = 'stock.rule'

    is_oxford_rule = fields.Boolean("Is Oxford Rule")
    is_oxford_rule_web = fields.Boolean("Is Oxford Rule Website")


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    freight_id = fields.Many2one(comodel_name="freight.freight", string="Logistics Records")

    @api.model
    def run_test(self, procurements, raise_user_error=True):

        """
        *** DEPRECATED ***

        OVERRIDE: Override for creating outer company transfer directly from sale order

        Fulfil `procurements` with the help of stock rules.

        Procurements are needs of products at a certain location. To fulfil
        these needs, we need to create some sort of documents (`stock.move`
        by default, but extensions of `_run_` methods allow to create every
        type of documents).

        :param procurements: the description of the procurement
        :type list: list of `~odoo.addons.stock.models.stock_rule.ProcurementGroup.Procurement`
        :param raise_user_error: will raise either an UserError or a ProcurementException
        :type raise_user_error: boolan, optional
        :raises UserError: if `raise_user_error` is True and a procurement isn't fulfillable
        :raises ProcurementException: if `raise_user_error` is False and a procurement isn't fulfillable
        """

        def raise_exception(procurement_errors):
            if raise_user_error:
                dummy, errors = zip(*procurement_errors)
                raise UserError('\n'.join(errors))
            else:
                raise ProcurementException(procurement_errors)

        actions_to_run = defaultdict(list)
        procurement_errors = []
        for procurement in procurements:
            procurement.values.setdefault('company_id', procurement.location_id.company_id)
            procurement.values.setdefault('priority', '0')
            procurement.values.setdefault('date_planned', fields.Datetime.now())
            if (
                procurement.product_id.type not in ('consu', 'product') or
                float_is_zero(procurement.product_qty, precision_rounding=procurement.product_uom.rounding)
            ):
                continue
            rule = self._get_rule(procurement.product_id, procurement.location_id, procurement.values)

            # Overriden Portion Start ==========================================

            # All Other Orders
            if self._context.get('is_oxford_process') and self._context.get(
                    'is_sale_order_process') and not self._context.get('is_processed_oxford'):
                rule = rule.search([('is_oxford_rule', '=', True), ('sequence', '=', 1)], limit=1) or rule
                self = self.with_context(is_processed_oxford=1)
                rule = rule.with_context(is_processed_oxford=1)
            elif self._context.get('is_oxford_process') and self._context.get(
                    'is_sale_order_process') and self._context.get('is_processed_oxford'):
                is_processed_oxford = self._context.get('is_processed_oxford') + 1 or 1
                rule = rule.search([('is_oxford_rule', '=', True), ('sequence', '=', is_processed_oxford)],
                                   limit=1) or rule
                self = self.with_context(is_processed_oxford=is_processed_oxford)
                rule = rule.with_context(is_processed_oxford=is_processed_oxford)

            # DS Orders
            if self._context.get('is_oxford_process_web') and self._context.get(
                    'is_sale_order_process_web') and not self._context.get('is_processed_oxford_web'):
                rule = rule.search([('is_oxford_rule_web', '=', True), ('sequence', '=', 1)], limit=1) or rule
                self = self.with_context(is_processed_oxford_web=1)
                rule = rule.with_context(is_processed_oxford_web=1)
            elif self._context.get('is_oxford_process_web') and self._context.get(
                    'is_sale_order_process_web') and self._context.get('is_processed_oxford_web'):
                is_processed_oxford_web = self._context.get('is_processed_oxford_web') + 1 or 1
                rule = rule.search([('is_oxford_rule_web', '=', True), ('sequence', '=', is_processed_oxford_web)],
                                   limit=1) or rule
                self = self.with_context(is_processed_oxford_web=is_processed_oxford_web)
                rule = rule.with_context(is_processed_oxford_web=is_processed_oxford_web)

            # Overriden Portion End ==========================================

            if not rule:
                error = _('No rule has been found to replenish "%s" in "%s".\nVerify the routes configuration on the product.') %\
                    (procurement.product_id.display_name, procurement.location_id.display_name)
                procurement_errors.append((procurement, error))
            else:
                action = 'pull' if rule.action == 'pull_push' else rule.action
                actions_to_run[action].append((procurement, rule))

        if procurement_errors:
            raise_exception(procurement_errors)

        for action, procurements in actions_to_run.items():
            if hasattr(self.env['stock.rule'], '_run_%s' % action):
                try:
                    getattr(self.env['stock.rule'], '_run_%s' % action)(procurements)
                except ProcurementException as e:
                    procurement_errors += e.procurement_exceptions
            else:
                _logger.error("The method _run_%s doesn't exist on the procurement rules" % action)

        if procurement_errors:
            raise_exception(procurement_errors)
        return True
