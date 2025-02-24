/** @odoo-module **/

import session from "web.session";
import config from "web.config";
import { _t } from "web.core";
import { SignableDocument, SignInfoDialog, ThankYouDialog } from '@sign/js/common/document_signable';

function deleteQueryParamFromURL(param) {
    let url = new URL(location.href);
    url.searchParams.delete(param);
    window.history.replaceState(null, '', url);
}

/**
 * Processes special errors from the IAP server
 * @param { String } errorMessage
 * @returns { [String, Boolean] } error message, title or false
 */
function processErrorMessage(errorMessage) {
    const defaultTitle = false;
    const errorMap = {
        "err_connection_odoo_instance": [
            _t("The itsme® identification data could not be forwarded to Odoo, the signature could not be saved."),
            defaultTitle
        ],
        "access_denied": [
            _t("You have rejected the identification request or took too long to process it. You can try again to finalize your signature."),
            _t("Identification refused")
        ]
    };
    return errorMap[errorMessage] ? errorMap[errorMessage] : [ errorMessage, defaultTitle ]
}

const ItsmeDialog = SignInfoDialog.extend({
    template: "sign_itsme.itsme_dialog",
    events: {
        "click .itsme_confirm": function() {
            this.onItsmeClick.bind(this.getParent())()
        },
        "click .itsme_cancel": function() {
            this.close();
        }
    },

    onItsmeClick: async function () {
        const [route, params] = this._getRouteAndParams();
        return session.rpc(route, params).then(({success, authorization_url, message}) => {
            if (success) {
                if (authorization_url) {
                    window.location.replace(authorization_url);
                } else {
                    this.openThankYouDialog();
                }
            } else {
                this.openErrorDialog (
                    message,
                    () => {
                        window.location.reload();
                    }
                );
            }
        });
    },

    renderElement: function () {
        this._super.apply(this, arguments);
        this.$modal.addClass("o_sign_thank_you_dialog");
        this.$modal.find("button.btn-close").addClass("invisible");
    },

    init: function (parent, requestID, requestToken, signature, newSignItems, options) {
        options = options || {};
        if (config.device.isMobile) {
            options.fullscreen = true;
        }
        options.title = _t("Confirm your identity");
        options.size = options.size || "medium";
        options.renderFooter = false;
        this._super(parent, options);
        this.requestID = requestID;
        this.requestToken = requestToken;
        this.signature = signature;
        this.newSignItems = newSignItems;
        this.buttons = [];
     }
});

SignableDocument.include({
    start: async function () {
        const res = this._super(this, arguments);
        this.showThankYouDialog = this.$("#o_sign_show_thank_you_dialog").length > 0;
        this.errorMessage = this.$("#o_sign_show_error_message").val();
        if (this.errorMessage) {
            const [errorMessage, title] = processErrorMessage(this.errorMessage);
            this.openErrorDialog(errorMessage, () => {
                deleteQueryParamFromURL('error_message');
            }, title);
        }
        if (this.showThankYouDialog) {
            this.openThankYouDialog();
        }
        return res;
    },
    getAuthDialog: async function () {
        if (this.authMethod === 'itsme') {
            const credits = await session.rpc('/itsme/has_itsme_credits');
            if (credits) {
                return new ItsmeDialog (
                    this,
                    this.requestID,
                    this.accessToken,
                    this.signInfo.signatureValues,
                    this.signInfo.newSignItems,
                    {
                        nextSign: this.name_list.length
                    }
                );
            }
            return false;
        }

        return this._super(this, arguments);
    }
});

ThankYouDialog.include({
    viewDocument: function() {
        if (this.getParent().showThankYouDialog) {
            deleteQueryParamFromURL('show_thank_you_dialog')
            return this.close();
        }
        return this._super(this, arguments);
    }
})
