/** @odoo-module */
import AccountReport from 'account_reports.account_report'
import { retrieveHMRCClientInfo } from "../../hmrc_api";

AccountReport.accountReportsWidget.include({
    renderButtons: function() {
        this._super();
        var self = this;
        this.buttonsOptions = this.report_options.buttons;

        for(let buttonsOptionIndex in this.buttonsOptions) {
            let buttonOption = this.buttonsOptions[buttonsOptionIndex];
            let el = this.$buttons.siblings('button')[buttonsOptionIndex]
            if (buttonOption.client_tag === 'send_hmrc_button_report') {
                $(el).unbind('click').click(
                    function() {
                        self.$buttons.attr('disabled', true);
                        self.odoo_context.client_data = retrieveHMRCClientInfo()

                        return self._rpc({
                            model: 'account.report',
                            method: 'dispatch_report_action',
                            args: [self.report_options.report_id, self.report_options, $(el).attr('action')],
                            context: self.odoo_context
                        })
                        .then(function(result){
                            if (result.help) {
                                result.help = owl.markup(result.help)
                            }
                            var doActionProm = self.do_action(result);
                            self.$buttons.attr('disabled', false);
                            return doActionProm;
                        })
                        .guardedCatch(function() {
                            self.$buttons.attr('disabled', false);
                        });
                    }
                )
            }
        }
    },
});
