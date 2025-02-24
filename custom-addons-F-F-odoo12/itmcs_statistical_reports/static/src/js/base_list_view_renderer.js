odoo.define('itmcs_statistical_reports.ListRenderer', function (require) {
"use strict";
var BasicRenderer = require('web.BasicRenderer');
var ListRenderer = require('web.ListRenderer');

var ListRendererExtended = ListRenderer.include({

        init: function (parent, state, params) {
          this._super.apply(this, arguments);
        },
        _computeColumnAggregates: function (data, column) {

        var attrs = column.attrs;
        var field = this.state.fields[attrs.name];
        if (!field) {
            return;
        }
        var type = field.type;
        if (type !== 'integer' && type !== 'float' && type !== 'monetary') {
            return;
        }
        var func = (attrs.sum && 'sum') || (attrs.avg && 'avg') ||
            (attrs.max && 'max') || (attrs.min && 'min');
        if (func) {
            var count = 0;
            var inv_qty = 0;
            var total_selling_price = 0;
            var total_sale_price = 0;
            var model = ''
            var aggregateValue = (func === 'max') ? -Infinity : (func === 'min') ? Infinity : 0;
            _.each(data, function (d) {
                count += 1;
                var value = (d.type === 'record') ? d.data[attrs.name] : d.aggregateValues[attrs.name];
                if (func === 'avg') {

                    if(d.model === 'sale.report' && attrs.name === 'standard_price'){

                       if (d.data.standard_price > 0){
                        inv_qty += d.data.qty_invoiced
                       }
                       total_selling_price += d.data.avg_cost
                       aggregateValue += d.data.qty_invoiced
                       if(model === ''){
                         model += d.model
                       }
                    }
                    else if (d.model === 'sale.report' && attrs.name === 'margin'){
                       total_selling_price += d.data.avg_cost
                       total_sale_price += d.data.price_unit * d.data.qty_invoiced
                       aggregateValue += total_sale_price
                       if(model === ''){
                         model += d.model
                       }
                    }
                    else if (d.model === 'sale.report' && attrs.name === 'price_unit'){
                       total_sale_price += d.data.price_unit * d.data.qty_invoiced
                       if (d.data.standard_price > 0){
                       inv_qty += d.data.qty_invoiced
                       }
                       aggregateValue += inv_qty
                       if(model === ''){
                         model += d.model
                       }
                    }
                    else{
                     aggregateValue += value;
                    }

                } else if (func === 'sum') {
                    aggregateValue += value;
                } else if (func === 'max') {
                    aggregateValue = Math.max(aggregateValue, value);
                } else if (func === 'min') {
                    aggregateValue = Math.min(aggregateValue, value);
                }
            });

            if (func === 'avg') {
                if(model === 'sale.report' && attrs.name === 'standard_price'){
                     aggregateValue = inv_qty ? total_selling_price / inv_qty : aggregateValue;
                }
                else if(model === 'sale.report' && attrs.name === 'margin'){
                     aggregateValue = total_sale_price ? 1-(total_selling_price / total_sale_price) : aggregateValue;
                }
                else if(model === 'sale.report' && attrs.name === 'price_unit'){
                     aggregateValue = inv_qty ? total_sale_price / inv_qty : aggregateValue;
                }
                else{
                    aggregateValue = count ? aggregateValue / count : aggregateValue;
                }
            }
            column.aggregate = {
                help: attrs[func],
                value: aggregateValue,
            };
        }
    },
});
return ListRendererExtended;
});
