odoo.define('invoice_payment_date.AveragePaymentDaysFooter', function (require) {
    "use strict";

     var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        _renderFooter: function () {
            var $footer = this._super.apply(this, arguments);
            var self = this;
            var totalDays = 0;
            var count = 0;
            var paymentDaysField = 'payment_days'; // Field name for Payment Days

            // Calculate total payment days and count records
            _.each(this.state.data, function (record) {
                var days = record.data[paymentDaysField];
                if (days !== undefined && !isNaN(days)) {
                    totalDays += days;
                    count += 1;
                }
            });

            var avgDays = count > 0 ? (totalDays / count).toFixed(2) : '0.00';

            // Log all columns for debugging
            console.log('Columns:', self.columns);

            // Identify the correct column index for Payment Days
            var columnIndex = -1;
            self.columns.forEach(function (column, index) {
                console.log('Column', index, ':', column); // Log each column
                if (column.name === paymentDaysField || column.field === paymentDaysField) {
                    columnIndex = index;
                }
            });

            console.log('Column index for', paymentDaysField, ':', columnIndex);

            // Ensure we have the correct footer row and cell
            var $footerRow = $footer.find('tr').last(); // Last row is usually the footer
            if ($footerRow.length) {
                var $footerCells = $footerRow.find('td');
                console.log('Footer cells:', $footerCells.length);

                if (columnIndex >= 0 && $footerCells.length > columnIndex) {
                    var $targetCell = $footerCells.eq(columnIndex);
                    $targetCell.text('Avg: ' + avgDays);
                } else {
                    console.warn('No footer cell found for index:', columnIndex);
                    
                    // Directly update the last footer cell if index is not found
                    var $lastCell = $footerCells.last();
                    if ($lastCell.length) {
                        $lastCell.text('Avg: ' + avgDays);
                    } else {
                        console.warn('No footer cell found to update directly.');
                    }
                }
            } else {
                console.warn('Footer row not found.');
            }

            return $footer;
        },
    });
});

