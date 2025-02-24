# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import pytz

from odoo import _, api, fields, models
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import OrderedSet
import logging
from odoo.tools import float_compare, float_is_zero

_logger = logging.getLogger("Inventory Counting")


class Inventory(models.Model):
    _name = "stock.inventory"
    _description = "Inventory"
    _order = "date desc, id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        'Inventory Reference', default="Inventory",
        readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    date = fields.Datetime(
        'Inventory Date',
        readonly=True, required=True,
        default=fields.Datetime.now,
        help="If the inventory adjustment is not validated, date at which the theoritical quantities have been checked.\n"
             "If the inventory adjustment is validated, date at which the inventory adjustment has been validated.")
    line_ids = fields.Many2many(
        'stock.quant', string='Inventories',
        copy=False, readonly=False,
        states={'done': [('readonly', True)]})
    move_ids = fields.Many2many(
        'stock.move', string='Stock Move',
        copy=False, readonly=False,
        states={'done': [('readonly', True)]})
    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'In Progress'),
        ('done', 'Validated')],
                             copy=False, index=True, readonly=True, tracking=True,
                             default='draft')
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, index=True, required=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env.company)
    location_ids = fields.Many2many(
        'stock.location', string='Locations',
        readonly=True, check_company=True,
        states={'draft': [('readonly', False)]},
        domain="[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit'])]")
    product_ids = fields.Many2many(
        'product.product', string='Products', check_company=True,
        domain="[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Specify Products to focus your inventory on particular Products.")
    start_empty = fields.Boolean('Empty Inventory',
                                 help="Allows to start with an empty inventory.")
    prefill_counted_quantity = fields.Selection(string='Counted Quantities',
                                                help="Allows to start with a pre-filled counted quantity for each lines or "
                                                     "with all counted quantities set to zero.", default='counted',
                                                selection=[('counted', 'Default to stock on hand'),
                                                           ('zero', 'Default to zero')])
    exhausted = fields.Boolean(
        'Include Exhausted Products', readonly=True,
        states={'draft': [('readonly', False)]},
        help="Include also products with quantity of 0")

    is_lock = fields.Boolean("Is Lock")

    inventory_line_ids = fields.One2many(
        'stock.inventory.line', 'inventory_id', string='Inventories',
        copy=False, readonly=False)

    def lock_inventory_count(self):
        self.is_lock = True

    def unlock_inventory_count(self):
        self.is_lock = False

    def _product_of_stock_inventory_category(self):
        domain = [('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)]
        for rec in self:
            if rec.env.context.get('is_inventory_count'):
                product = self.env['product.product'].search([('categ_id', '=', rec.stock_inventory_category.id)])
                if product:
                    domain.append(('id', 'in', product.ids))
        return domain

    def action_view_count_stock_move_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_line_action")

        self.ensure_one()

        # Define domains and context
        move_domain = [('location_dest_id.usage', 'in', ['internal', 'transit']),
                       ('company_id', '=', self.company_id.id)]

        if self.location_ids:
            domain_loc = [('id', 'child_of', self.location_ids.ids), ('company_id', '=', self.company_id.id)]
        else:
            domain_loc = [('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])]
        if self.warehouse_id:
            domain_loc.append(('warehouse_id', '=', self.warehouse_id.id))

        locations_ids = [l['id'] for l in self.env['stock.location'].search_read(domain_loc, ['id'])]

        if locations_ids:
            move_domain = expression.AND(
                [move_domain, ['|', ('location_id', 'in', locations_ids), ('location_dest_id', 'in', locations_ids)]])

        product_ids = self._get_product_domain(is_start_inventory=True)
        if self.product_ids:
            move_domain = expression.AND([move_domain, [('product_id', 'in', self.product_ids.ids)]])
        else:
            move_domain = expression.AND([move_domain, product_ids])

        if self.from_date_range:
            move_domain = expression.AND([move_domain, [('date', '>=', self.from_date_range)]])
        if self.to_date_range:
            move_domain = expression.AND([move_domain, [('date', '<=', self.to_date_range)]])

        action['domain'] = move_domain
        return action

    # product_ids = fields.Many2many(
    #     'product.product', string='Products', check_company=True,
    #     domain=_product_of_stock_inventory_category,
    #     readonly=True,
    #     states={'draft': [('readonly', False)]},
    #     help="Specify Products to focus your inventory on particular Products.")
    # domain = "[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    is_inventory_count = fields.Boolean(string="Is Inventory Count", copy=False, default=True)
    stock_inventory_category = fields.Many2one('product.category', string='Category', tracking=True)
    from_date_range = fields.Datetime('From Date', tracking=True)
    to_date_range = fields.Datetime('To Date', tracking=True, default=lambda self: fields.Datetime.now())
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', tracking=True)

    # @api.onchange('from_date_range')
    # def _onchange_from_date_range(self):
    #     for rec in self:
    #         if rec.from_date_range:
    #             user_tz = self.env.user.tz or pytz.utc
    #             local = pytz.timezone(user_tz)
    #             rec.from_date_range = str(rec.from_date_range)[:10] + ' 19:30:00'
    #
    # @api.onchange('to_date_range')
    # def _onchange_to_date_range(self):
    #     for rec in self:
    #         if rec.to_date_range:
    #             rec.to_date_range = str(rec.to_date_range)[:10] + ' 18:29:59'

    @api.onchange('warehouse_id', 'stock_inventory_category')
    def _onchange_domain_product_id(self):
        domain = []
        if self.env.context.get('is_inventory_count'):
            domain = self._get_product_domain(is_start_inventory=False)
        domain = expression.AND([domain, [('type', '=', 'product'), '|', ('company_id', '=', False),
                                          ('company_id', '=', self.env.company.id)]])
        return {'domain': {'product_ids': domain}}

    def _get_product_domain(self, is_start_inventory=False):
        product_domain = [('active', 'in', [False, True]), '|', ('company_ids', '!=', False),
                          ('company_ids', 'in', self.company_id.ids)]
        domain = []
        if self.warehouse_id:
            # stock_quant_id = self.env['stock.quant'].search(
            #     [('location_id.warehouse_id', '=', self.warehouse_id.id), ('location_id.usage', '=', 'internal')])
            product_ids = self.env['product.product'].search(product_domain)
            if product_ids and is_start_inventory:
                domain.append(('product_id', 'in', product_ids.ids))
            elif product_ids:
                domain.append(('id', 'in', product_ids.ids))
        if self.stock_inventory_category:
            product = self.env['product.product'].search([('categ_id', '=', self.stock_inventory_category.id)])
            if product and is_start_inventory:
                domain.append(('product_id', 'in', product.ids))
            elif product:
                domain.append(('id', 'in', product.ids))
        return domain

    @api.model
    def default_get(self, fields):
        is_inventory_count = self.env.context.get('is_inventory_count')
        vals = super(Inventory, self).default_get(fields)
        vals['is_inventory_count'] = is_inventory_count
        return vals

    def _get_quantities(self):
        """Return quantities group by product_id, location_id, lot_id, package_id and owner_id

        :return: a dict with keys as tuple of group by and quantity as value
        :rtype: dict
        """
        self.ensure_one()

        # Define domains and context
        domain = [('location_id.usage', 'in', ['internal', 'transit']), ('company_id', '=', self.company_id.id)]
        move_domain = [('location_dest_id.usage', 'in', ['internal', 'transit']),
                       ('company_id', '=', self.company_id.id)]

        if self.location_ids:
            domain_loc = [('id', 'child_of', self.location_ids.ids), ('company_id', '=', self.company_id.id)]
        else:
            domain_loc = [('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])]
        if self.warehouse_id:
            domain_loc.append(('warehouse_id', '=', self.warehouse_id.id))

        locations_ids = [l['id'] for l in self.env['stock.location'].search_read(domain_loc, ['id'])]

        if locations_ids:
            domain.append(('location_id', 'in', locations_ids))
            move_domain = expression.AND(
                [move_domain, ['|', ('location_id', 'in', locations_ids), ('location_dest_id', 'in', locations_ids)]])

        product_ids = self._get_product_domain(is_start_inventory=True)
        if self.product_ids:
            domain = expression.AND([domain, [('product_id', 'in', self.product_ids.ids)]])
            move_domain = expression.AND([move_domain, [('product_id', 'in', self.product_ids.ids)]])
        else:
            domain = expression.AND([domain, product_ids])
            move_domain = expression.AND([move_domain, product_ids])
        # domain = expression.AND([domain, [('quantity', '!=', 0)]])

        # move_domain = expression.AND([move_domain, [('qty_done', '!=', 0)]])

        if self.from_date_range:
            domain = expression.AND([domain, [('in_date', '>=', self.from_date_range)]])
            move_domain = expression.AND([move_domain, [('date', '>=', self.from_date_range)]])
        if self.to_date_range:
            domain = expression.AND([domain, [('in_date', '<=', self.to_date_range)]])
            move_domain = expression.AND([move_domain, [('date', '<=', self.to_date_range)]])

        fields = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'quantity:sum']
        group_by = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id']

        move_ids = self.env['stock.move.line'].search(move_domain)
        if move_ids:
            locations_ids = move_ids.location_dest_id + move_ids.location_id
            locations_ids = locations_ids.filtered(lambda l: l.usage == 'internal' and l.name not in ['Staging','Shipping Staging', 'Input', 'Output'])
            domain = [('product_id', 'in', move_ids.product_id.ids), ('location_id', 'in', locations_ids.ids)]

        quants = self.env['stock.quant'].read_group(domain, fields, group_by, lazy=False)
        return [{(
                    quant['product_id'] and quant['product_id'][0] or False,
                    quant['location_id'] and quant['location_id'][0] or False,
                    quant['lot_id'] and quant['lot_id'][0] or False,
                    quant['package_id'] and quant['package_id'][0] or False,
                    quant['owner_id'] and quant['owner_id'][0] or False):
                    quant['quantity'] for quant in quants
                }, move_ids]

    @api.onchange('company_id')
    def _onchange_company_id(self):
        # If the multilocation group is not active, default the location to the one of the main
        # warehouse.
        if not self.user_has_groups('stock.group_stock_multi_locations'):
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)
            if warehouse:
                self.location_ids = warehouse.lot_stock_id

    def copy_data(self, default=None):
        name = _("%s (copy)") % (self.name)
        default = dict(default or {}, name=name)
        return super(Inventory, self).copy_data(default)

    def unlink(self):
        for inventory in self:
            if (inventory.state not in ('draft', 'cancel')
                    and not self.env.context.get(MODULE_UNINSTALL_FLAG, False)):
                raise UserError(
                    _('You can only delete a draft inventory adjustment. If the inventory adjustment is not done, you can cancel it.'))
        return super(Inventory, self).unlink()

    def action_validate(self):
        # if not self.exists():
        #     return
        # self.ensure_one()
        # if not self.user_has_groups('stock.group_stock_manager'):
        #     raise UserError(_("Only a stock manager can validate an inventory adjustment."))
        # if self.state != 'confirm':
        #     raise UserError(_(
        #         "You can't validate the inventory '%s', maybe this inventory "
        #         "has been already validated or isn't ready.", self.name))
        # inventory_lines = self.line_ids.filtered(lambda l: l.inventory_quantity_set)
        # for rec in inventory_lines:
        #     rec.with_context(inventory_id=self).action_apply_inventory()
        #     _logger.info(
        #         f"Company ID: {rec.company_id and rec.company_id.id or ''} Warehouse ID: {rec.warehouse_id and rec.warehouse_id.id or ''} Location ID: {rec.location_id and rec.location_id.id or ''} Product ID: {rec.product_id and rec.product_id.id or ''}")
        # self.line_ids._check_company()
        # self._check_company()
        self.state = 'done'
        return True

    def action_check(self):
        """ Checks the inventory and computes the stock move to do """
        # tde todo: clean after _generate_moves
        for inventory in self.filtered(lambda x: x.state not in ('done', 'cancel')):
            # first remove the existing stock moves linked to this inventory
            inventory.with_context(prefetch_fields=False).mapped('move_ids').unlink()
            inventory.line_ids._generate_moves()

    def action_cancel_draft(self):
        self.line_ids = False
        self.inventory_line_ids.unlink()
        self.write({'state': 'draft'})

    def action_start(self):
        self.ensure_one()
        self._action_start()
        self._check_company()
        # action_set_inventory_quantity_to_zero
        res = self.with_context(start_inventory=True).action_open_inventory_lines()
        # domain = res.get('domain')
        # if domain and self.prefill_counted_quantity == 'zero':
        #     quant_ids = self.env['stock.quant'].search(domain)
        #     if quant_ids:
        #         quant_ids.action_set_inventory_quantity_to_zero()
        return res

    def _action_start(self):
        """ Confirms the Inventory Adjustment and generates its inventory lines
        if its state is draft and don't have already inventory lines (can happen
        with demo data or tests).
        """
        for inventory in self:
            if inventory.state != 'draft':
                continue
            vals = {
                'state': 'confirm',
                'date': fields.Datetime.now()
            }
            inventory.write(vals)

    def action_open_inventory_lines(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'name': _('Inventory Lines'),
            # 'res_model': 'stock.quant',
            'res_model': 'stock.inventory.line',
        }
        context = {
            'is_inventory_count': True,
            'default_is_editable': True,
            'default_company_id': self.company_id.id,
        }

        action['view_id'] = self.env.ref('stock_inventory_count_tus.stock_inventory_line_tree').id
        if not self.inventory_line_ids:
            self.env['stock.inventory.line'].create(self._get_inventory_lines_values())
        action['context'] = context
        action['domain'] = [('inventory_id', '=', self.id)]
        return action

    def action_print(self):
        return self.env.ref('stock.action_report_inventory').report_action(self)

    def _get_exhausted_inventory_lines_vals(self, non_exhausted_set):
        """Return the values of the inventory lines to create if the user
        wants to include exhausted products. Exhausted products are products
        without quantities or quantity equal to 0.

        :param non_exhausted_set: set of tuple (product_id, location_id) of non exhausted product-location
        :return: a list containing the `stock.quant` values to create
        :rtype: list
        """
        self.ensure_one()
        if self.product_ids:
            product_ids = self.product_ids.ids
        else:
            product_ids = self.env['product.product'].search_read([
                '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False),
                ('type', '=', 'product'),
                ('active', '=', True)], ['id'])
            product_ids = [p['id'] for p in product_ids]

        if self.location_ids:
            location_ids = self.location_ids.ids
        else:
            location_ids = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)]).lot_stock_id.ids

        vals = []
        for product_id in product_ids:
            for location_id in location_ids:
                if ((product_id, location_id) not in non_exhausted_set):
                    vals.append({
                        'inventory_id': self.id,
                        'product_id': product_id,
                        'location_id': location_id,
                        'theoretical_qty': 0
                    })
        return vals

    def _get_inventory_lines_values(self):
        """Return the values of the inventory lines to create for this inventory.

        :return: a list containing the `stock.quant` values to create
        :rtype: list
        """
        self.ensure_one()
        get_quantities = self._get_quantities()
        quants_groups = get_quantities[0]
        move_ids = get_quantities[1]
        vals = []
        product_ids = OrderedSet()
        for (product_id, location_id, lot_id, package_id, owner_id), quantity in quants_groups.items():
            temp_lines = move_ids.filtered(lambda m: m.product_id.id == product_id)
            temp_location_ids = temp_lines.mapped('location_id') + temp_lines.mapped('location_dest_id')
            if location_id in temp_location_ids.ids:
                line_values = {
                    'inventory_id': self.id,
                    'qty_done': 0 if self.prefill_counted_quantity == "zero" else quantity,
                    'theoretical_qty': quantity,
                    'prod_lot_id': lot_id,
                    'partner_id': owner_id,
                    'product_id': product_id,
                    'location_id': location_id,
                    'package_id': package_id
                }
                product_ids.add(product_id)
                vals.append(line_values)
        product_id_to_product = dict(zip(product_ids, self.env['product.product'].browse(product_ids)))
        for val in vals:
            val['product_uom_id'] = product_id_to_product[val['product_id']].product_tmpl_id.uom_id.id
        if self.exhausted:
            vals += self._get_exhausted_inventory_lines_vals({(l['product_id'], l['location_id']) for l in vals})
        return vals

    def _get_stock_inventory_lines_values(self, move_ids):
        """Return the values of the inventory lines to create for this inventory.

        :return: a list containing the `stock.inventory.line` values to create
        :rtype: list
        """
        self.ensure_one()
        vals = []
        product_ids = OrderedSet()
        prefill_counted_quantity = self.prefill_counted_quantity != 'zero'
        for move in move_ids:
            existing_updated = False
            for val in vals:
                if move.product_id.id == val.get('product_id') and move.location_dest_id.id == val.get(
                        'location_dest_id'):
                    val['qty_done'] += prefill_counted_quantity and move.qty_done or 0
                    val['theoretical_qty'] += move.qty_done or 0
                    existing_updated = True
                    break
            if existing_updated:
                continue
            line_values = {
                'inventory_id': self.id,
                'qty_done': prefill_counted_quantity and move.qty_done or 0,
                'theoretical_qty': move.qty_done,
                'prod_lot_id': move.lot_id.id,
                'product_id': move.product_id.id,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
                'package_id': move.package_id.id
            }
            product_ids.add(move.product_id.id)
            vals.append(line_values)
        product_id_to_product = dict(zip(product_ids, self.env['product.product'].browse(product_ids)))
        for val in vals:
            val['product_uom_id'] = product_id_to_product[val['product_id']].product_tmpl_id.uom_id.id
        if self.exhausted:
            vals += self._get_exhausted_inventory_lines_vals({(l['product_id'], l['location_dest_id']) for l in vals})
        return vals


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _apply_inventory(self):
        if self._context and self._context.get('inventory_id'):
            inventory_id = self._context.get('inventory_id')
            move_vals = []
            if not self.user_has_groups('stock.group_stock_manager'):
                raise UserError(_('Only a stock manager can validate an inventory adjustment.'))
            for quant in self:
                # Create and validate a move so that the quant matches its `inventory_quantity`.
                if float_compare(quant.inventory_diff_quantity, 0,
                                 precision_rounding=quant.product_uom_id.rounding) > 0:
                    move_vals.append(
                        quant._get_inventory_move_values(quant.inventory_diff_quantity, quant.product_id.with_company(
                            quant.company_id).property_stock_inventory, quant.location_id))
                else:
                    move_vals.append(quant._get_inventory_move_values(-quant.inventory_diff_quantity, quant.location_id,
                                                                      quant.product_id.with_company(
                                                                          quant.company_id).property_stock_inventory,
                                                                      out=True))
            moves = self.env['stock.move'].with_context(inventory_mode=False).create(move_vals)
            moves._action_done()
            inventory_id.write({'move_ids': [(6, 0, inventory_id.move_ids.ids + moves.ids)]})
            self.location_id.write({'last_inventory_date': fields.Date.today()})
            date_by_location = {loc: loc._get_next_inventory_date() for loc in self.mapped('location_id')}
            for quant in self:
                quant.inventory_date = date_by_location[quant.location_id]
            self.write({'inventory_quantity': 0, 'user_id': False})
            self.write({'inventory_diff_quantity': 0})
        else:
            return super(StockQuant, self)._apply_inventory()


class InventoryLine(models.Model):
    _name = "stock.inventory.line"
    _description = "Inventory Line"
    _order = "product_id, inventory_id, prod_lot_id"

    @api.model
    def _domain_location_id(self):
        if self.env.context.get('active_model') == 'stock.inventory':
            inventory = self.env['stock.inventory'].browse(self.env.context.get('active_id'))
            if inventory.exists() and inventory.location_ids:
                return "[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit']), ('id', 'child_of', %s)]" % inventory.location_ids.ids
        return "[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit'])]"

    @api.model
    def _domain_product_id(self):
        if self.env.context.get('active_model') == 'stock.inventory':
            inventory = self.env['stock.inventory'].browse(self.env.context.get('active_id'))
            if inventory.exists() and len(inventory.product_ids) > 1:
                return "[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id), ('id', 'in', %s)]" % inventory.product_ids.ids
        return "[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"

    def _search_difference_qty(self, operator, value):
        if not self._context.get('active_ids'):
            raise NotImplementedError(_('Unsupported search on %s outside of an Inventory Adjustment', 'difference_qty'))
        value = abs(float(value or 0))
        lines = self.search([('inventory_id', 'in', self._context.get('active_ids'))])
        if operator == '=':
            line_ids = lines.filtered(lambda l: abs(l.difference_qty) == value)
        elif operator == '!=':
            line_ids = lines.filtered(lambda l: abs(l.difference_qty) != value)
        elif operator == '>':
            line_ids = lines.filtered(lambda l: abs(l.difference_qty) > value)
        elif operator == '<':
            line_ids = lines.filtered(lambda l: abs(l.difference_qty) < value)
        elif operator == '>=':
            line_ids = lines.filtered(lambda l: abs(l.difference_qty) >= value)
        elif operator == '<=':
            line_ids = lines.filtered(lambda l: abs(l.difference_qty) <= value)
        else:
            line_ids = lines.filtered(lambda l: abs(l.difference_qty) == value)
        return [('id', 'in', line_ids.ids)]

    is_editable = fields.Boolean(help="Technical field to restrict editing.")
    inventory_id = fields.Many2one(
        'stock.inventory', 'Inventory', check_company=True,
        index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', 'Owner', check_company=True)
    product_id = fields.Many2one(
        'product.product', 'Product', check_company=True,
        domain=lambda self: self._domain_product_id(),
        index=True, required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        required=True, readonly=True)
    qty_done = fields.Float(
        'Counted Quantity', states={'done': [('readonly', False)]},
        digits='Product Unit of Measure', default=0)
    categ_id = fields.Many2one(related='product_id.categ_id', store=True)
    location_id = fields.Many2one(
        'stock.location', 'Location', check_company=True,
        index=True, required=True)
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location', check_company=True,
        domain=lambda self: self._domain_location_id(),
        index=True, required=False)
    package_id = fields.Many2one(
        'stock.quant.package', 'Pack', index=True, check_company=True)
    prod_lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial Number', check_company=True,
        domain="[('product_id','=',product_id), ('company_id', '=', company_id)]")
    company_id = fields.Many2one(
        'res.company', 'Company', related='inventory_id.company_id',
        index=True, readonly=True, store=True)
    state = fields.Selection(string='Status', related='inventory_id.state')
    theoretical_qty = fields.Float(
        'Theoretical Quantity',
        digits='Product Unit of Measure', readonly=True)
    difference_qty = fields.Float('Difference', compute='_compute_difference',
                                  help="Indicates the gap between the product's theoretical quantity and its newest quantity.",
                                  readonly=True, digits='Product Unit of Measure', search="_search_difference_qty")
    inventory_date = fields.Datetime('Inventory Date', readonly=True,
                                     default=fields.Datetime.now,
                                     help="Last date at which the On Hand Quantity has been computed.")
    outdated = fields.Boolean(string='Quantity outdated',
                              compute='_compute_outdated', search='_search_outdated')
    product_tracking = fields.Selection(string='Tracking', related='product_id.tracking', readonly=True)

    @api.depends('qty_done', 'theoretical_qty')
    def _compute_difference(self):
        for line in self:
            line.difference_qty = line.qty_done - line.theoretical_qty

    @api.depends('inventory_date', 'product_id.stock_move_ids', 'theoretical_qty', 'product_uom_id.rounding')
    def _compute_outdated(self):
        quants_by_inventory = {inventory: inventory._get_quantities()[0] for inventory in self.inventory_id}
        for line in self:
            quants = quants_by_inventory[line.inventory_id]
            if line.state == 'done' or not line.id:
                line.outdated = False
                continue
            qty = quants.get((
                line.product_id.id,
                line.location_dest_id.id,
                line.prod_lot_id.id,
                line.package_id.id,
                line.partner_id.id), 0
            )
            if float_compare(qty, line.theoretical_qty, precision_rounding=line.product_uom_id.rounding) != 0:
                line.outdated = True
            else:
                line.outdated = False

    def _search_outdated(self, operator, value):
        if operator != '=':
            if operator == '!=' and isinstance(value, bool):
                value = not value
            else:
                raise NotImplementedError()
        if not self.env.context.get('default_inventory_id'):
            raise NotImplementedError(_('Unsupported search on %s outside of an Inventory Adjustment', 'outdated'))
        lines = self.search([('inventory_id', '=', self.env.context.get('default_inventory_id'))])
        line_ids = lines.filtered(lambda line: line.outdated == value).ids
        return [('id', 'in', line_ids)]
