from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    edi_sale_line_name = fields.Text(related='sale_line_id.name')

    edi_pack_qualifier = fields.Selection(string='EDI Pack Qualifier', selection=[('OU', 'Outer Pack'), ('IN', 'Inner Pack'), ('CA', 'Consumer Package')], default='OU', help='Code identifying the type of packaging; Part of the <Packaging> field on the EDI file.')
    consumer_package_code = fields.Char(string='Consumer Package Code (EDI)', related='sale_line_id.edi_consumer_package_code',
                              help='Consumer Package Code passed from the EDI. We store it because sometimes it contains leading or training zeros that we need to transmit outbound. When searching for a product sometimes we need to strip these zeros to find the match.')
    edi_line_sequence_number = fields.Char(string='Line Sequence Number', related='sale_line_id.edi_line_sequence_number',
                              help='For an initiated document, this is a unique number for the line item[s]. For a return transaction, this number should be the same as what was received from the source transaction. Example: You received a Purchase Order with the first LineSequenceNumber of 10. You would then send back an Invoice with the first LineSequenceNumber of 10')
    edi_buyer_part_number = fields.Char(string='Buyer Part Number', related='product_id.edi_buyer_part_number',
                              help='Buyer\'s primary product identifier')
    edi_vendor_part_number = fields.Char(string='Vendor Part Number', related='product_id.edi_vendor_part_number',
                              help='Vendor\'s primary product identifier')
    edi_part_number = fields.Char(string='Part Number',
                              help='Vendor\'s part number. Belongs to the <ProductID> field on the EDI file.')
    edi_item_status_code = fields.Selection(related='sale_line_id.edi_item_status_code')
    edi_qty_cases = fields.Float(related='sale_line_id.edi_qty_cases')
    done_cases = fields.Float(string='Done Cases', compute='_compute_done_cases')
    ordered_cases = fields.Float(string='Ordered Cases', compute='_compute_ordered_cases')
    edi_uom = fields.Char(related='sale_line_id.edi_uom')
    edi_lot_name = fields.Char(string='EDI Lot Name')
    edi_reference_qual = fields.Selection(selection= [
        ('CN', 'Carrier Pro Number'),
        ('GK', 'Third Party Reference Number'),
        ('WU', 'Vessel'),
        ('87', 'Functional Category'),
        ('OC', 'Ocean Container Number'),], string='EDI Reference Qualifier', default='CN')

    edi_company_warehouse_id = fields.Many2one(string='EDI Company Warehouse', comodel_name='res.partner', compute='_compute_edi_company_warehouse_id')

    def _compute_edi_company_warehouse_id(self):
        for record in self:
            company_warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', record.company_id.id)], limit=1)
            if not company_warehouse_id:
                company_warehouse_id = self.company_id.ids[0]
            record.edi_company_warehouse_id = company_warehouse_id.partner_id

    @api.depends('product_uom_qty')
    def _compute_done_cases(self):
        for record in self:
            if record.product_uom_qty and record.product_id and record.product_id.packaging_ids and record.product_id.packaging_ids[0].qty:
                record.done_cases = float(record.product_uom_qty / record.product_id.packaging_ids[0].qty)
            else:
                record.done_cases = record.product_uom_qty

    @api.depends('product_id.packaging_ids.qty')
    def _compute_ordered_cases(self):
        for record in self:
            if record.product_id.packaging_ids and record.product_id.packaging_ids[0].qty:
                record.ordered_cases = float(record.product_uom_qty / record.product_id.packaging_ids[0].qty)
            else:
                record.ordered_cases = 0


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    consumer_package_code = fields.Char(string='Consumer Package Code (EDI)',
                              help='Consumer Package Code passed from the EDI. We store it because sometimes it contains leading or training zeros that we need to transmit outbound. When searching for a product sometimes we need to strip these zeros to find the match.',
                              related='move_id.consumer_package_code')

    edi_line_sequence_number = fields.Char(string='Line Sequence Number',
                              help='For an initiated document, this is a unique number for the line item[s]. For a return transaction, this number should be the same as what was received from the source transaction. Example: You received a Purchase Order with the first LineSequenceNumber of 10. You would then send back an Invoice with the first LineSequenceNumber of 10')
    edi_buyer_part_number = fields.Char(string='Buyer Part Number',
                              help='Buyer\'s primary product identifier',
                              related='move_id.edi_buyer_part_number')

    edi_vendor_part_number = fields.Char(string='Vendor Part Number',
                              help='Vendor\'s primary product identifier',
                              related='move_id.edi_vendor_part_number')

    edi_part_number = fields.Char(string='Part Number',
                            help='Vendor\'s part number. Belongs to the <ProductID> field on the EDI file.',
                            related='move_id.edi_part_number'
                              )

    done_cases = fields.Float(related='move_id.done_cases')
    ordered_cases = fields.Float(related='move_id.ordered_cases')
    edi_uom = fields.Char(related='move_id.edi_uom')

    edi_lot_name = fields.Char(string='EDI Lot Name', related='move_id.edi_lot_name', store=True)


    def write(self, vals):
        res = super().write(vals)
        for stock_move_line in self:
            if not stock_move_line.edi_line_sequence_number:
                existing_nums = self.picking_id.move_line_ids_without_package.sorted(
                    key=lambda r: int(r.edi_line_sequence_number), reverse=True).mapped('edi_line_sequence_number')
                num = str(int(existing_nums[0]) + 1) if existing_nums else '1'
                stock_move_line.write({'edi_line_sequence_number': num})
        return res
