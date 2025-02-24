/* @odoo-module */

import { registry } from "@web/core/registry";
import { X2ManyField } from "@web/views/fields/x2many/x2many_field";
import { MappingListRenderer } from '../mapping_list_renderer/mapping_list_renderer';

const { onWillStart } = owl;

export class MappingField extends X2ManyField {

}

MappingField.components = {
    ...X2ManyField.components,
    ListRenderer: MappingListRenderer,
}

registry.category("fields").add("form.mapping_widget", MappingField);