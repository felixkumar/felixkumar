from odoo import fields, models, api

class AccountMoveInvoiceReport(models.Model):
    _inherit = "account.move"

    @api.model
    def get_line_items(self):
        line_item = []
        line = 1
        for rec in self.invoice_line_ids:
            data_line = {
                'line': line,
                'item': rec.product_id.default_code,
                'description': rec.name,
                'quantity': rec.quantity,
                'uom': rec.product_uom_id.name,
                'unit_price': rec.price_unit,
                'taxes': sum(tax.amount for tax in rec.tax_ids),  # Assuming taxes are percentage values
                'line_taxes': [tax.amount for tax in rec.tax_ids],
                'total_price': rec.price_subtotal
            }
            line_item.append(data_line)
            line += 1
        return line_item

    @api.model
    def get_chunked_line_items(self, chunk_size=10):
        items = self.get_line_items()
        chunked_items = []
        running_total = 0

        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            subtotal = sum(item['total_price'] for item in chunk)
            running_total += subtotal
            total_taxes = sum(item['taxes'] * item['total_price'] / 100 for item in chunk)  # Calculating the tax amount
            chunked_items.append({
                'lines': chunk,
                'subtotal': subtotal,
                'running_total': running_total,
                'tax': total_taxes
            })
            final_total = {
                'total': running_total,
                'total_taxes': total_taxes
            }
        return chunked_items
