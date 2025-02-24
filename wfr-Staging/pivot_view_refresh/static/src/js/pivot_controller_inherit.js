/** @odoo-module **/

import { PivotController } from "@web/views/pivot/pivot_controller";
import { patch } from "@web/core/utils/patch";
const { onMounted } = owl;

patch(PivotController.prototype, "pivot_controller_refresh",{
    setup(){
        this._super();
        onMounted(this._mounted);
    },

     _mounted(){
        if (document.querySelector('.reload_view') !== null){
            document.querySelector('.reload_view').addEventListener('click', this.pivot_reload_view.bind(this));
        }
    },
    pivot_reload_view: function () {
        this.view_update();
   },

   async view_update() {
        console.log('Reloading...')
        const metaData = this.model._buildMetaData();
        const config = { metaData, data: this.model.data };
        await this.model._loadData(config);
        this.render(true);
   },

});