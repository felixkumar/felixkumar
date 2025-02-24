odoo.define('ks_dashboard_ninja.import_button', function(require) {

    "use strict";

    var core = require('web.core');
    var _t = core._t;
    var Sidebar = require('web.Sidebar');
    var ListController = require('web.ListController');
    var framework = require('web.framework');
    var Dialog = require('web.Dialog');


    ListController.include({



        // TO add custom dashboard export option under action button
        renderSidebar: function($node) {
            var self = this;
            //Only for our custom model
            if (this.modelName == "ks_dashboard_ninja.board") {
                if (this.hasSidebar) {
                    var other = [{
                        label: _t("Export Dashboard"),
                        callback: this.ks_dashboard_export.bind(this)
                    }];
                    if (this.archiveEnabled) {
                        other.push({
                            label: _t("Archive"),
                            callback: function() {
                                Dialog.confirm(self, _t("Are you sure that you want to archive all the selected records?"), {
                                    confirm_callback: self._toggleArchiveState.bind(self, true),
                                });
                            }
                        });
                        other.push({
                            label: _t("Unarchive"),
                            callback: this._toggleArchiveState.bind(this, false)
                        });
                    }
                    if (this.is_action_enabled('delete')) {
                        other.push({
                            label: _t('Delete'),
                            callback: this._onDeleteSelectedRecords.bind(this)
                        });
                    }
                    this.sidebar = new Sidebar(this, {
                        editable: this.is_action_enabled('edit'),
                        env: {
                            context: this.model.get(this.handle, {
                                raw: true
                            }).getContext(),
                            activeIds: this.getSelectedIds(),
                            model: this.modelName,
                        },
                        actions: _.extend(this.toolbarActions, {
                            other: other
                        }),
                    });
                    return this.sidebar.appendTo($node).then(function() {
                        self._toggleSidebar();
                    });
                }
                return Promise.resolve();
            } else {
                this._super.apply(this, arguments);
            }
        },

        ks_dashboard_export: function() {
            this.ks_on_dashboard_export(this.getSelectedIds());
        },

        ks_on_dashboard_export: function(ids) {
            var self = this;
            this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'ks_dashboard_export',
                args: [JSON.stringify(ids)],
            }).then(function(result) {
                var name = "dashboard_ninja";
                var data = {
                    "header": name,
                    "dashboard_data": result,
                }
                framework.blockUI();
                self.getSession().get_file({
                    url: '/ks_dashboard_ninja/export/dashboard_json',
                    data: {
                        data: JSON.stringify(data)
                    },
                    complete: framework.unblockUI,
                    error: (error) => this.call('crash_manager', 'rpc_error', error),
                });
            })
        },


    });
    core.action_registry.add('ks_dashboard_ninja.import_button', ListController);
    return ListController;
});