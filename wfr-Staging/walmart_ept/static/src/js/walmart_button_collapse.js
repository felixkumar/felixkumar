odoo.define('walmart_ept.walmart_collapse_button', function (require) {
"use strict";
    var core = require('web.core');
    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');
    var viewRegistry = require('web.view_registry');
    var _t = core._t;

    var collapseButtonKanbanController = KanbanController.extend({_dropZone: '.o_kanban_record'}, {
        events: _.extend({}, KanbanController.prototype.events, {
            'click #walmart_button_toggle': '_toggleBtn',
        }),
        /**
         * To toggle the OnBoarding button to hide /show the panel
         */
        _toggleBtn: _.debounce(function (ev) {
            var self = this
            return this._rpc({
                model: 'res.company',
                method: 'action_toggle_walmart_instances_onboarding_panel',
                args: [parseInt(ev.currentTarget.getAttribute('data-company-id'))],
            }).then(function(result) {
                if(result == 'closed'){
                    $('.o_onboarding_container.collapse').collapse('hide')
                    $('#walmart_button_toggle').html('Create more Walmart instance').css({"background-color":"#ececec","border":"1px solid #ccc"});
                } else {
                    $('.o_onboarding_container.collapse').collapse('show')
                    $('#walmart_button_toggle').html('Hide On boarding Panel').css({"background-color":"","border": ""});
                }
            }).guardedCatch(function (error) {
                self.do_warn(_t('Warning'), _t('Something Went Wrong'));
            });
        }, 300),
    });

    var WalmartOnBoardingToggleKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: collapseButtonKanbanController,
        }),
    });

    viewRegistry.add('WalmartOnBoardingToggle', WalmartOnBoardingToggleKanbanView);
});
