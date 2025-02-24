/** @odoo-module **/
import { browser } from '@web/core/browser/browser';
import { useComponentToModel } from '@mail/component_hooks/use_component_to_model';
import { useService } from "@web/core/utils/hooks";
import { registerMessagingComponent } from '@mail/utils/messaging_component';

const { Component } = owl;

export class PrintnodeStatusMenu extends Component {
    /**
    * @override
    */
    async setup() {
        super.setup();

        this.user = useService("user");

        useComponentToModel({ fieldName: 'component' });
    }

    get printnodeStatusMenu() {
        return this.props.record;
    }

    get currentWorkstationId() {
        let workstationId = browser.localStorage.getItem('printnode_base.workstation_id');
        return workstationId;
    }

    setWorkstationDevice(e) {
        const workstationId = e.target.value;

        if (workstationId) {
            browser.localStorage.setItem('printnode_base.workstation_id', workstationId);
            this.user.updateContext({ 'printnode_workstation_id': parseInt(workstationId) });
        } else {
            browser.localStorage.removeItem('printnode_base.workstation_id');

            if ('printnode_workstation_id' in this.user.context) {
                this.user.removeFromContext('printnode_workstation_id');
            }
        }

        // Reload data in model
        this.props.record._fetchData();
    }
}

Object.assign(PrintnodeStatusMenu, {
    props: { record: Object },
    template: 'printnode_base.StatusMenu',
});

registerMessagingComponent(PrintnodeStatusMenu);
