/** @odoo-module */

import { KanbanRenderer } from '@web/views/kanban/kanban_renderer';
import { useService } from '@web/core/utils/hooks';
import * as BarcodeScanner from '@web/webclient/barcode/barcode_scanner';
import { bus } from 'web.core';

const { onWillStart } = owl;

export class StockBarcodeKanbanRenderer extends KanbanRenderer {
    setup() {
        super.setup(...arguments);
        const user = useService('user');
        this.display_protip = this.props.list.resModel === 'stock.picking';
        onWillStart(async () => {
            this.packageEnabled = await user.hasGroup('stock.group_tracking_lot');
            this.isMobileScanner = BarcodeScanner.isBarcodeScannerSupported();
        });
    }

    async openMobileScanner() {
        const barcode = await BarcodeScanner.scanBarcode();
        if (barcode) {
            bus.trigger('barcode_scanned', barcode);
            if ('vibrate' in window.navigator) {
                window.navigator.vibrate(100);
            }
        } else {
            this.env.services.notification.add(
                this.env._t("Please, Scan again !"),
                {type: 'warning'}
            );
        }
    }

}
StockBarcodeKanbanRenderer.template = 'stock_barcode.KanbanRenderer';
