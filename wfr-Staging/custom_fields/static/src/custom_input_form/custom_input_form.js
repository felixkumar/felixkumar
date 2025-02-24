/** @odoo-module **/

import publicWidget from "web.public.widget";

/*
* The method to change input fields attributes when type of the record is changed
*/
function _redefineVisibility(InstanceType) {
    var FieldsCheckIDS = document.querySelectorAll(".type_visibility_depend");       

    _.each(FieldsCheckIDS, function (field) {
        var inputs = field.getElementsByClassName("s_website_form_input");       
        if (inputs && inputs.length != 0) {
            var input = inputs[0];
            var AvailableTypes = input.getAttribute("invisible");
            if (AvailableTypes) {
                var AvailableTypesArray = AvailableTypes.split(",");
                var anyIntersectionArray = AvailableTypesArray.filter(value => InstanceType.includes(value));
                if (anyIntersectionArray.length > 0) {
                    field.removeAttribute("style");
                    // In case of double change a field should become required back
                    if (input.getAttribute("needrequired") == "True") {
                        input.setAttribute("required", "True");
                    };
                }
                else {
                    field.setAttribute("style", "display: none;");
                    if (input.getAttribute("required") == "True") {
                        input.removeAttribute("required");
                        input.setAttribute("needrequired", "True");
                    }
                };
            };
        };
    });
};

/*
* The widget applied to the special field type. So, when it is changed to apply changes to the field
*/
publicWidget.registry.contactTypeForm = publicWidget.Widget.extend({
    selector: ".select_type_input",
    /*
    * The method to find the custom type field and add events to that
    */
    start: function () {
        var customTypes = document.querySelectorAll("select.select_type_input");
        if (customTypes.length !== 0) {
            var currentValue = customTypes[0].value;
            if (currentValue) {
                currentValue = [customTypes[0].value.toString()]
            }
            else {
                currentValue = [0]
            };
            _redefineVisibility(currentValue);
            customTypes[0].addEventListener("change", function (ev) {
                var InstanceType = [0]
                if (ev.currentTarget.value) {
                    // in case of select2, types might be multiple, so we should split that
                    InstanceType = ev.currentTarget.value.split(",");
                }
                _redefineVisibility(InstanceType);
            });
        }
        else {_redefineVisibility(0);};
    },
});
