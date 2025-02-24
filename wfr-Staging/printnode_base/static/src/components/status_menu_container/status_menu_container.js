/** @odoo-module **/

import session from 'web.session';

import { attr } from '@mail/model/model_field';
import { getMessagingComponent } from "@mail/utils/messaging_component";
import { registerModel } from '@mail/model/model_core';
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";

import { MANAGER_GROUP } from '../../js/constants';

// Ensure nested components are registered beforehand
import '@printnode_base/components/status_menu_view/status_menu_view';

const { Component } = owl;

registerModel({
    name: 'PrintnodeStatusMenuModel',
    lifecycleHooks: {
        async _created() {
            // Do initial fetch of data. This is required to know if there are new releases
            // available to show different menu item.
            await this._fetchData(true);

            document.addEventListener('click', this._onClickCaptureGlobal, true);
        },
        _willDelete() {
            document.removeEventListener('click', this._onClickCaptureGlobal, true);
        },
    },
    recordMethods: {
        close() {
            this.update({ isOpen: false });
        },

        async _fetchData(onlyReleases = false) {
            this.update({ loaded: false });

            if (this.printnodeEnabled) {
                // We check if current user has Manager group to make some elements of status menu
                // visible only for managers
                const isManager = await session.user_has_group(MANAGER_GROUP);
                const data = await this.messaging.rpc({
                    model: 'printnode.base',
                    method: 'get_status',
                    kwargs: { 'only_releases': onlyReleases },
                });

                this.update({
                    isManager,
                    limits: data.limits,
                    releases: data.releases,
                    devices: data.devices,
                    workstations: data.workstations,
                    rateUsURL: this._prepareRateUsURL(),
                });
            }
            this.update({ loaded: true });
        },

        _prepareRateUsURL() {
            // Rate Us URL
            let odooVersion = odoo.info.server_version;
            // This attribute can include some additional symbols we do not need here (like 12.0e+)
            odooVersion = odooVersion.substring(0, 4);

            return `https://apps.odoo.com/apps/modules/${odooVersion}/printnode_base/#ratings`;
        },

        /**
         * @param {MouseEvent} ev
         */
        async onClickDropdownToggle(ev) {
            ev.preventDefault();
            if (this.isOpen) {
                this.update({ isOpen: false });
            } else {
                this.update({
                    loaded: false,
                    isOpen: true,
                });

                // Reload data on each open
                this._fetchData();
            }
        },
        /**
         * Closes the menu when clicking outside, if appropriate.
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onClickCaptureGlobal(ev) {
            if (!this.exists()) {
                return;
            }
            if (!this.component || !this.component.root.el) {
                return;
            }
            if (this.component.root.el.contains(ev.target)) {
                return;
            }
            this.close();
        },
        /**
         * @private
         * @returns {FieldCommand}
         */
        _computeActivityGroupViews() {
            return this.activityGroups.map(activityGroup => {
                return {
                    activityGroup,
                };
            });
        },
    },
    fields: {
        releases: attr({ default: [] }),
        limits: attr({ default: [] }),
        devices: attr({ default: {} }),
        workstations: attr({ default: [] }),
        component: attr(),
        rateUsURL: attr(),
        isOpen: attr({
            default: false,
        }),
        isManager: attr({
            default: false
        }),
        loaded: attr({
            default: false
        }),
        printnodeEnabled: attr({
            default: session.dpc_user_enabled,
        }),
    },
});


export class PrintnodeStatusMenuContainer extends Component {

    /**
     * @override
     */
    async setup() {
        super.setup();

        this.messaging = useService("messaging");
        this.messaging.get().then((messaging) => {
            this.printnodeStatusMenu = messaging.models['PrintnodeStatusMenuModel'].insert();
            this.render();
        });
    }

}

Object.assign(PrintnodeStatusMenuContainer, {
    components: { PrintnodeStatusMenu: getMessagingComponent('PrintnodeStatusMenu') },
    template: 'printnode_base.StatusMenuContainer',
});

registry.category('systray').add('printnode_base.PrintnodeStatusMenuContainer', {
    Component: PrintnodeStatusMenuContainer,
});