/** @odoo-module **/

import { TemplateDialog } from "@documents_spreadsheet/spreadsheet_template/spreadsheet_template_dialog";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

import { XLSX_MIME_TYPES } from "@documents_spreadsheet/helpers";

export const DocumentsSpreadsheetControllerMixin = {
    setup() {
        this._super(...arguments);
        this.action = useService("action");
        this.dialogService = useService("dialog");
        // Hack-ish way to do this but the function is added by a hook which we can't really override.
        this.baseOnOpenDocumentsPreview = this.onOpenDocumentsPreview.bind(this);
        this.onOpenDocumentsPreview = this._onOpenDocumentsPreview.bind(this);
    },

    /**
     * @override
     */
    async _onOpenDocumentsPreview({ mainDocument }) {
        if (mainDocument.data.handler === "spreadsheet") {
            this.action.doAction({
                type: "ir.actions.client",
                tag: "action_open_spreadsheet",
                params: {
                    spreadsheet_id: mainDocument.resId,
                },
            });
        } else if (XLSX_MIME_TYPES.includes(mainDocument.data.mimetype)) {
            this.dialogService.add(ConfirmationDialog, {
                body: _t(
                    "Your file is about to be saved as an Odoo Spreadsheet to allow for edition."
                ),
                confirm: async () => {
                    const spreadsheetId = await this.orm.call(
                        "documents.document",
                        "clone_xlsx_into_spreadsheet",
                        [mainDocument.resId]
                    );
                    this.action.doAction({
                        type: "ir.actions.client",
                        tag: "action_open_spreadsheet",
                        params: {
                            spreadsheet_id: spreadsheetId,
                        },
                    });
                },
            });
        } else {
            return this.baseOnOpenDocumentsPreview(...arguments);
        }
    },

    async onClickCreateSpreadsheet(ev) {
        this.dialogService.add(TemplateDialog, {
            folderId: this.env.searchModel.getSelectedFolderId(),
            context: this.props.context,
        });
    },
};
