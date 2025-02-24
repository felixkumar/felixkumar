/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
const { Component, onWillStart, onWillUnmount, useState } = owl;


export class SuggestedProduct extends Component {
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.state = useState({ qty: this.props.qty, price: this.props.price, reloadState: false });
    }
    /*
    * Getter for qtyValue
    */
    get qtyValue() {
        return this.state.qty.toString();
    }
    /*
    * The method to add one unit
    */
    async _onButtonChange(substracted=false) {
        var currentQty = this.state.qty;
        if (substracted) { currentQty -= 1 }
        else { currentQty += 1 };
        await this._changeQuantity(currentQty > 0 ? currentQty : 0);
    }
    /*
    * The method to process manual unput change
    */
    async _onChangeQuantity(event) {
        const currentQty = parseFloat(event.currentTarget.value);
        await this._changeQuantity(currentQty || this.state.qty)
    }
    /*
    * The method to update state (trigger rerender) and calculate price if necessary
    */
    async _changeQuantity(newQty) {
        var productPrice = "";
        if (this.props.pricelist) {
            productPrice = await this.props.manageRpc(
                "/business_appointment/suggested_product_price",
                { product_id: this.props.id, pricelist_id: this.props.pricelist, qty: newQty },
            );
        };
        Object.assign(this.state, {
            qty: newQty,
            price: productPrice,
            reloadState: !this.state.reloadState, // hack to rerender even if there have been no chabges
        })
        this.props.onUpdateState(this.props.id, newQty)
    }
};
SuggestedProduct.template = "business_appointment.SuggestedProduct";


export class SuggestedProductsDialog extends Component {
    /*
    * Re-write to introduce own services and actions
    */
    setup() {
        this.title = this.env._t("Complementary Products");
        this.size = "lg";
        this.resultSuggested = {};
        this.finalProducts = false;
        onWillStart(() => {
            if (this.props.suggestedProducts && this.props.suggestedProducts.length) {
                for (const suggestedProduct of this.props.suggestedProducts) {
                    this.resultSuggested[suggestedProduct.id] = suggestedProduct.qty;
                };
            };
        });
        onWillUnmount(() => { this.props.finishReservation(this.finalProducts) });
    }
    /*
    * The method to save changes done in lines
    */
    onUpdateState(productId, newQty) {
        this.resultSuggested[productId] = newQty;
    }
    /*
    * The method to save the dialog and get back to the orig
    */
    onAddProducts() {
        this.finalProducts = [];
        for (const [key, value] of Object.entries(this.resultSuggested)) {
            if (value != 0) {
                this.finalProducts.push([0, 0, { product_id: parseInt(key), product_uom_qty: value} ])
            }
        };
        this.props.close();
    }
};

SuggestedProductsDialog.template= "business_appointment.SuggestedProductsDialog"
SuggestedProductsDialog.components = { Dialog, SuggestedProduct }
