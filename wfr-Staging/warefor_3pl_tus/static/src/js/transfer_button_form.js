odoo.define('transfer_button_near_create_form_new.form_button', function(require) {
   "use strict";
   var FormController = require('web.FormController');
   var FormView = require('web.FormView');
   var viewRegistry = require('web.view_registry');
   var FormButton = FormController.include({
       buttons_template: 'transfer_button_near_create_form_new.button',
       events: _.extend({}, FormController.prototype.events, {
           'click .action_picking_form_new': '_OpenFormTransfer',
       }),
       init: function (parent, model, renderer, params) {
       debugger
       this._super.apply(this, arguments);
       if (params.controlPanel){
               this.button_form_enable_it = params.controlPanel.props.view.arch.attrs.button_form_enable_it
       }
       },
       _OpenFormTransfer: function () {
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
   }
   });
   var FreightFormView = FormView.extend({
       config: _.extend({}, FormView.prototype.config, {
           Controller: FormButton
       }),
   });
   viewRegistry.add('button_in_form', FreightFormView);
});