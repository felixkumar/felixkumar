from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
BLOCK_USER = [1580]


class PartnerAvailableQuantity(models.Model):
    _name = 'partner.available.quantity'
    _rec_name = 'partner_id'
    _description = 'Partner Available Product Quantity'

    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner", required=False, )
    product_line_ids = fields.One2many(comodel_name="available.quantity.line", inverse_name="available_qty_id",
                                       string="Partner Quantity Line", required=False, )

    @api.depends('product_line_ids')
    def _compute_product(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for partner in self:
            partner.total_product = len(partner.product_line_ids.mapped('product_id'))
            partner.total_qty = sum(partner.product_line_ids.mapped('qty'))

    total_product = fields.Integer(string="Total Product", required=False, compute="_compute_product")
    total_qty = fields.Integer(string="Total Qty", required=False, compute="_compute_product")

    def partner_available_product(self):
        self.search([]).unlink()
        partner_ids = self.env['res.partner'].search([])
        for partner in partner_ids:
            data = {}
            picking_ids = self.env['stock.picking'].search([('state', '=', 'done'), ('partner_id', '=', partner.id)])
            if not picking_ids:
                continue
            line_list = []
            for line_id in picking_ids.move_line_ids_without_package:
                if line_id.product_id.type != 'product':
                    continue
                if line_id.picking_code == "incoming":
                    if data.get(line_id.product_id.id):
                        data[line_id.product_id.id] = data[line_id.product_id.id] + line_id.qty_done
                        continue
                    data.update({line_id.product_id.id: line_id.qty_done})
                if line_id.picking_code == "outgoing":
                    if data.get(line_id.product_id.id):
                        data[line_id.product_id.id] = data[line_id.product_id.id] - line_id.qty_done
                        continue
                    data.update({line_id.product_id.id: -(line_id.qty_done)})
            new_record = self.create({'partner_id': partner.id})
            for rec in data.items():
                line_val = (0, 0, {
                    'product_id': rec[0],
                    'qty': rec[1],
                    'available_qty_id': new_record.id
                })
                line_list.append(line_val)
            new_record.write({"product_line_ids": line_list})

    @api.model
    def get_views(self, views, options=None):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            options['toolbar'] = False
        res = super().get_views(views, options)
        # if self.env.user.id in BLOCK_USER and res.get('views'):
        #     if res.get('views', {}).get('list', {}).get('arch', "") and 'tree' in res.get('views', {}).get('list',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['list']['arch']
        #         data = data.replace("tree", 'tree create="false"', 1)
        #         res['views']['list']['arch'] = data
        #     if res.get('views', {}).get('form', {}).get('arch', "") and 'form' in res.get('views', {}).get('form',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['form']['arch']
        #         data = data.replace("form", 'form create="false"', 1)
        #         res['views']['form']['arch'] = data
        #     if res.get('views', {}).get('kanban', {}).get('arch', "") and 'kanban' in res.get('views', {}).get('kanban',
        #                                                                                                        {}).get(
        #             'arch', ""):
        #         data = res['views']['kanban']['arch']
        #         data = data.replace("kanban", 'kanban create="false"', 1)
        #         res['views']['kanban']['arch'] = data
        return res

    def write(self, vals):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            raise UserError("You don't have enough access, Please contact your system administrator.")
        res = super(PartnerAvailableQuantity, self).write(vals)
        return res


class AvailableQuantityLine(models.Model):
    _name = 'available.quantity.line'
    _rec_name = 'product_id'
    _description = 'Available Quantity Line'

    available_qty_id = fields.Many2one(comodel_name="partner.available.quantity", string="Available Quantity",
                                       required=False, ondelete='cascade')
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )
    qty = fields.Integer(string="Quantity", required=False, )
