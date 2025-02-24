/** @odoo-module **/

import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";


export class ResourcesMany2Many extends Many2ManyTagsField {
    /*
    * Re-write to add own services and actions
    */
    setup() {
        this.orm = useService("orm");
        super.setup(...arguments);
    }
    /*
    * The method to choose any resource of the chosen resource type
    */
    async _onClickAnyResources() {
        const recordData = this.props.record.data;
        const resourceIDS = this._convertFormData("many2many", recordData.resource_ids);
        const resourceTypeID = this._convertFormData("many2one", recordData.resource_type_id);
        const resources = await this.orm.call("business.resource.type", "action_return_ba_resources", [[resourceTypeID], resourceIDS]);
        if (resources) {
            await this.props.record.model.root.update(_.object(["resource_ids"], [{
                operation: "ADD_M2M", ids: resources,
            }]));
        }; 
    }
    /*
    * The method to convert form data to real ids
    */
    _convertFormData(fieldType, fieldValue) {
        if (fieldType == "many2one") {
            return fieldValue && fieldValue.length != 0 ? fieldValue[0] : false  
        }
        else if (fieldType == "many2many") {
            return fieldValue.records.map((record) => record.resId);
        };
    }
};

ResourcesMany2Many.supportedTypes = ["html"];
ResourcesMany2Many.template = "business_appointment.ResourcesMany2Many";
ResourcesMany2Many.props = { ...Many2ManyTagsField.props };

registry.category("fields").add("resource_many2many", ResourcesMany2Many);
