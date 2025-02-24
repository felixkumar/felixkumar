odoo.define('list_export_excel_app.ExcelButton',function(require){
	"use strict";

var ListView = require('web.ListView');
var ListController = require('web.ListController')
var ListRenderer = require('web.ListRenderer')
var rpc = require('web.rpc');

 
ListController.include({
		init: function () {
			this._super.apply(this, arguments);
			var button = this.$buttons
			if (this.selectedRecords.length = 0)
				button.style.visibility = "visible"
		},
		renderButtons: function() {
			this._super.apply(this, arguments)
			if(this.$buttons) {
					this.$buttons.on('click', '.button_export', this._onCreateExcel.bind(this));
			}		
		},

		_onCreateExcel: function (event, node) {

			var self = this;
		        var lst=[];
		        var res = [];
		        var model = "";
		        var field_val = [];
		        var fields_row = [];
		        var strings = [];
		        var fields_string = [];
		        var selection_fields = [];
		        var field = this.renderer.state.fields;
		        var records = _.map(this.selectedRecords, function (id) { 
		        return self.model.localData[id];
		        });
		        
		        for(var x =0;x<records.length;x++)
		        {
		           	lst.push(records[x]['data']['id']);
		           	model = records[x]['model']

		           	field_val = records[x]['fieldsInfo']['list']
		           	for(var key in field_val){
			           		var value = field_val[key]
			           		if (! value['invisible'] || value['modifiers']['column_invisible'] == false){
			           			fields_row.push(value['name'])
		           		}
		           	}	
		        }		       
		        
		        for (var j = 0; j < fields_row.length; j++){
				    if (field.hasOwnProperty(key)) {           
				        for (var key in field){
				        	if(fields_row[j] == key){
						        if (field[key]['type'] == 'selection'){
						        	selection_fields.push(field[key]['selection'])			        	
						        }
				        		fields_string.push(field[key]['string'])
				        	}
				        }
				    }
				}

				var fields_row_unique = [...new Set(fields_row)]
		        var fields_string_unique = [...new Set(fields_string)]

				rpc.query({
					model:'xls.excel',
					method:'create_excel',
					args:[1,lst,model,fields_string_unique,fields_row_unique,selection_fields],
				})
				.then(function (output) {
						
					self.do_action({
						type:'ir.actions.act_window',
						res_model:'sale.excel',
						res_id:output,
						target:'new',
						views:[[false, 'form']],
						view_type:'form',
						view_mode:'form',
						domain:[['id','=',output]]
					})
				});
			
		}
	});
});
