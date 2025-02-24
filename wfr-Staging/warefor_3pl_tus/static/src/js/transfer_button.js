odoo.define('transfer_button_near_create.kanban_button', function(require) {
   "use strict";
   var KanbanController = require('web.KanbanController');
   var KanbanView = require('web.KanbanView');
   var viewRegistry = require('web.view_registry');
   var core = require('web.core');
   var qweb = core.qweb;

   var KanbanButton = KanbanController.include({
       buttons_template: 'transfer_button_near_create.button',
       events: _.extend({}, KanbanController.prototype.events, {
           'click .action_picking_form': '_OpenWizardKanban',
       }),
       init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        if(params.controlPanel){
                this.button_enable_it = params.controlPanel.props.view.arch.attrs.button_enable_it
        }
        },
       _OpenWizardKanban: function () {
       var self = this;
        this.do_action({
           type: 'ir.actions.act_window',
           res_model: 'warefor.internal.transfer',
           name :'Internal Transfer',
           view_mode: 'form',
           view_type: 'form',
           views: [[false, 'form']],
           target: 'current',
           res_id: false,
       });
   },
   renderButtons: function ($node) {
        if (!this.hasButtons ) {
            return;
        }
        this.$buttons = $(qweb.render(this.buttons_template, {
            btnClass: 'btn-primary',
            widget: this,
        }));
        this.$buttons.on('click', 'button.o-kanban-button-new', this._onButtonNew.bind(this));
        this.$buttons.on('keydown', this._onButtonsKeyDown.bind(this));
        if ($node) {
            this.$buttons.appendTo($node);
        }

        if(!this.is_action_enabled('create')){
            this.$buttons.find('.o-kanban-button-new').remove()
        }
    },
   });
   var FreightKanbanView = KanbanView.extend({
       config: _.extend({}, KanbanView.prototype.config, {
           Controller: KanbanButton
       }),
   });
   viewRegistry.add('button_in_kanban', FreightKanbanView);
});