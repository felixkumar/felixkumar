/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { retrieveHMRCClientInfo } from "../../hmrc_api";

const { Component } = owl;

export class SendHmrcButton extends Component {
    setup() {
        this.orm = useService("orm");
        this.title = this.env._t('Send Data to the HMRC Service');
        this.hmrcGovClientDeviceIdentifier = this.props.record.data.hmrc_gov_client_device_id;
    }

    async retrieveClientInfo() {
        let clientData = retrieveHMRCClientInfo();
        clientData.hmrc_gov_client_device_id = this.hmrcGovClientDeviceIdentifier;
        await this.orm.call(
            'l10n_uk.vat.obligation',
            'action_submit_vat_return',
            [this.props.record.data.obligation_id[0], clientData]
        );
    }
}

SendHmrcButton.template = "l10n_uk_reports.SendHmrcButton";

registry.category('view_widgets').add('send_hmrc_button', SendHmrcButton);
