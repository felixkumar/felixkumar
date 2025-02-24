/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { FormViewDialog } from '@web/views/view_dialogs/form_view_dialog';
import Wysiwyg from 'web_editor.wysiwyg';
import { preserveCursor, closestElement } from '@web_editor/js/editor/odoo-editor/src/OdooEditor';

const { Component } = owl;

Wysiwyg.include({
    _getPowerboxOptions: function () {
        const options = this._super.apply(this, arguments);
        const {commands, categories} = options;
        categories.push({ name: _t('Navigation'), priority: 40 });
        commands.push(
            {
                category: _t('Navigation'),
                name: _t('Appointment'),
                priority: 10,
                description: _t('Add a specific appointment.'),
                fontawesome: 'fa-calendar',
                callback: async () => {
                    const selection = this.odooEditor.document.getSelection();
                    const anchorNode = selection && selection.anchorNode;
                    const restoreSelection = preserveCursor(this.odooEditor.document);
                    Component.env.services.dialog.add(AppointmentFormViewDialog, {
                        resModel: 'appointment.invite',
                        context: {
                            form_view_ref: "appointment.appointment_invite_view_form_insert_link",
                            default_appointment_type_ids: [],
                            default_staff_user_ids: [],
                        },
                        title: _t("Insert Appointment Link"),
                        mode: "edit",
                        insertLink: (url) => {
                            this.focus();
                            restoreSelection();
                            const label = _t('Schedule an Appointment');
                            const existingLink = closestElement(anchorNode, 'a');
                            if (existingLink) {
                                existingLink.setAttribute('href', url);
                                existingLink.textContent = label;
                                this.odooEditor.historyStep();
                            } else {
                                const link = document.createElement('a');
                                link.setAttribute('href', url);
                                link.textContent = label;
                                this.odooEditor.execCommand('insert', link);
                            }
                        },
                    });
                },
            },
            {
                category: _t('Navigation'),
                name: _t('Calendar'),
                priority: 10,
                description: _t('Schedule an appointment.'),
                fontawesome: 'fa-calendar',
                callback: () => {
                    const label = _t('Our Appointment Types');
                    const url = `${window.location.origin}/appointment`;
                    const selection = this.odooEditor.document.getSelection();
                    const anchorNode = selection && selection.anchorNode;
                    const existingLink = closestElement(anchorNode, 'a');
                    if (existingLink) {
                        existingLink.setAttribute('href', url);
                        existingLink.textContent = label;
                    } else {
                        const link = document.createElement('a');
                        link.setAttribute('href', url);
                        link.textContent = label;
                        this.odooEditor.execCommand('insert', link);
                    }
                },
            },
        );
        return {...options, commands, categories};
    }
});

class AppointmentFormViewDialog extends FormViewDialog {
    setup() {
        super.setup();
        this.viewProps.insertLink = this.props.insertLink;
        this.viewProps.closeDialog = this.props.close;
    }
}
AppointmentFormViewDialog.props = {
    ...FormViewDialog.props,
    insertLink: { type: Function },
};

class AppointmentInsertLinkFormController extends FormController {
    async beforeExecuteActionButton(clickParams) {
        if (clickParams.special) {
            if (clickParams.special === "save") { // Insert Link button
                const saved = await this.model.root.save();
                if (saved) {
                    this.props.insertLink(this.model.root.data.book_url);
                } else {
                    return false;
                }
            }
            this.props.closeDialog();
            return false;
        }
        return super.beforeExecuteActionButton(...arguments);
    }
}
AppointmentInsertLinkFormController.props = {
    ...FormController.props,
    insertLink: { type: Function },
    closeDialog: { type: Function },
};
registry.category("views").add("appointment_insert_link_form", {
    ...formView,
    Controller: AppointmentInsertLinkFormController,
});
