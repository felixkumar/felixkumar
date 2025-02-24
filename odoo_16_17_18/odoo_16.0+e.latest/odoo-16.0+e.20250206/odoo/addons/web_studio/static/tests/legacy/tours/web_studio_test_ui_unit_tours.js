/** @odoo-module */
import tour from "web_tour.tour";

tour.register(
    "web_studio_test_form_view_not_altered_by_studio_xml_edition",
    {
        test: true,
        url: "/web",
        sequence: 260
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            trigger: ".o_form_view .o_form_editable"
        },
        {
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_view"
        },
        {
            trigger: ".o_web_studio_xml_editor"
        },
        {
            extra_trigger: ".o_ace_view_editor",
            trigger: ".o_web_studio_leave"
        },
        {
            trigger: ".o_form_view .o_form_editable"
        }
    ]
);

/* global ace */
tour.register(
    "web_studio_test_edit_with_xml_editor",
    {
        test: true,
        url: "/web",
        sequence: 260
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            extra_trigger: ".someDiv",
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_view"
        },
        {
            trigger: ".o_web_studio_xml_editor"
        },
        {
            extra_trigger: ".o_ace_view_editor",
            trigger: ".select2-container:not(.d-none)",
            run() {
                const aceViewList = document.querySelector("#ace-view-list");
                const studioViewItem = Array.from(aceViewList.querySelectorAll("option")).filter(
                    (el) => {
                        return el.textContent.includes("Odoo Studio");
                    }
                )[0];

                if (!studioViewItem) {
                    throw new Error("There is no studio view");
                }

                const select2 = $(aceViewList).select2();
                select2.val(studioViewItem.value).trigger("change");
            }
        },
        {
            trigger: ".ace_content",
            run() {
                ace.edit("ace-view-editor").setValue("<data/>");
            }
        },
        {
            trigger: ".o_ace_view_editor .o_button_section [data-action='save']"
        },
        {
            trigger: ".o_web_studio_snackbar_icon:not('.fa-spin')"
        },
        {
            trigger: ".o_form_view",
            run() {
                if (document.querySelector(".someDiv")) {
                    throw new Error("The edition of the view's arch via the xml editor failed");
                }
            }
        }
    ]
);

tour.register(
    "web_studio_enter_x2many_edition_and_add_field",
    {
        test: true,
        sequence: 260
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            trigger: ".o_form_view .o_form_editable"
        },
        {
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_form_view_editor .o_field_widget[name='user_ids']",
        },
        {
            extra_trigger: ".o-web-studio-edit-x2manys-buttons",
            trigger: ".o_web_studio_editX2Many[data-type='form']"
        },
        {
            extra_trigger: ".o_web_studio_breadcrumb .breadcrumb-item:contains('Subview Form')",
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_header"
        },
        {
            extra_trigger: ".o_web_studio_existing_fields_section:not(.d-none)",
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='User log entries']",
            run() {
                $(".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='User log entries']")[0].scrollIntoView();
            }
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='User log entries']",
            run: "drag_and_drop (.o_web_studio_form_view_editor .o_web_studio_hook:eq(1))",
        },
        {
            trigger: ".o_web_studio_form_view_editor .o_field_widget[name='log_ids']",
            run() {
                const countFields = document.querySelectorAll(".o_web_studio_form_view_editor .o_field_widget").length;
                if (!countFields === 2) {
                    throw new Error("There should be 2 fields in the form view")
                }
            }
        }
    ]
);

tour.register(
    "web_studio_enter_x2many_auto_inlined_subview",
    {
        test: true,
        sequence: 260
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            trigger: ".o_form_view .o_form_editable"
        },
        {
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_form_view_editor .o_field_widget[name='user_ids'] .o_field_x2many_list",
        },
        {
            extra_trigger: ".o-web-studio-edit-x2manys-buttons",
            trigger: ".o_web_studio_editX2Many[data-type='list']"
        },
        {
            extra_trigger: ".o_web_studio_breadcrumb .breadcrumb-item:contains('Subview List')",
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_header"
        },
        {
            extra_trigger: ".o_web_studio_existing_fields_section:not(.d-none)",
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='User log entries']",
            run() {
                $(".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='User log entries']")[0].scrollIntoView();
            }
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='User log entries']",
            run: "drag_and_drop (.o_web_studio_list_view_editor .o_web_studio_hook:eq(1))",
        },
        {
            trigger: ".o_web_studio_list_view_editor th[data-name='log_ids']",
            run() {
                const countFields = document.querySelectorAll(".o_web_studio_form_view_editor th[data-name]").length;
                if (!countFields === 2) {
                    throw new Error("There should be 2 fields in the form view")
                }
            }
        }
    ]
);

tour.register(
    "web_studio_enter_x2many_auto_inlined_subview_with_multiple_field_matching",
    {
        test: true,
        sequence: 260
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            trigger: ".o_form_view .o_form_editable"
        },
        {
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_form_view_editor .o_field_widget[name='user_ids']:eq(1) .o_field_x2many_list",
        },
        {
            extra_trigger: ".o-web-studio-edit-x2manys-buttons",
            trigger: ".o_web_studio_editX2Many[data-type='list']"
        },
        {
            extra_trigger: ".o_web_studio_breadcrumb .breadcrumb-item:contains('Subview List')",
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_header"
        },
        {
            extra_trigger: ".o_web_studio_existing_fields_section:not(.d-none)",
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='User log entries']",
            run() {
                $(".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='User log entries']")[0].scrollIntoView();
            }
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='User log entries']",
            run: "drag_and_drop (.o_web_studio_list_view_editor .o_web_studio_hook:eq(1))",
        },
        {
            trigger: ".o_web_studio_list_view_editor th[data-name='log_ids']",
            run() {
                const countFields = document.querySelectorAll(".o_web_studio_form_view_editor th[data-name]").length;
                if (!countFields === 2) {
                    throw new Error("There should be 2 fields in the form view")
                }
            }
        }
    ]
);

tour.register(
    "we_studio_boolean_field_drag_and_drop",
    {
        test: true,
        url: "/web",
        sequence: 260
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            trigger: ".o_form_view .o_form_editable"
        },
        {
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_new_fields .o_web_studio_field_boolean",
            run: "drag_and_drop (.o_web_studio_form_view_editor .o_web_studio_hook:eq(0))",
        },
        {
            extra_trigger: ".o_web_studio_form_view_editor",
            trigger: ".o_wrap_field_boolean .o_wrap_label",
            run: "drag_and_drop_native (.o_web_studio_form_view_editor .o_web_studio_hook:eq(2))",
        },
        {
            trigger: ".o_wrap_label:eq(1):contains('New Checkbox')",
        },
    ]
);

tour.register(
    "web_studio_field_with_group",
    {
        test: true,
        sequence: 260
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            trigger: ".o_list_view"
        },
        {
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_list_view_editor th[data-name='function']",
            run() {}
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_header"
        },
        {
            extra_trigger: ".o_web_studio_existing_fields_section:not(.d-none)",
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='Website Link']",
            run() {
                $(".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='Website Link']")[0].scrollIntoView();
            }
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='Website Link']",
            run: "drag_and_drop (.o_web_studio_list_view_editor th.o_web_studio_hook:eq(2))",
        },
        {
            extra_trigger: ".o_web_studio_list_view_editor th.o_web_studio_hook:not(.o_web_studio_nearest_hook)",
            trigger: ".o_web_studio_list_view_editor th[data-name='website']",
            run() {
                const countFields = document.querySelectorAll(".o_web_studio_list_view_editor th[data-name]").length;
                if (!countFields === 3) {
                    throw new Error("There should be 3 fields in the form view")
                }
            }
        }
    ]
);

tour.register(
    "web_studio_elements_with_groups_form",
    {
        test: true,
        sequence: 260
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            trigger: ".o_form_view"
        },
        {
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_form_view_editor",
            run() {}
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_header"
        },
        {
            extra_trigger: ".o_web_studio_existing_fields_section:not(.d-none)",
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='Website Link']",
            run() {
                $(".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='Website Link']")[0].scrollIntoView();
            }
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='Website Link']",
            run: "drag_and_drop (.o_web_studio_form_view_editor .o_inner_group .o_web_studio_hook:eq(1))",
        },
        {
            extra_trigger: ".o_web_studio_form_view_editor .o_web_studio_hook:not(.o_web_studio_nearest_hook)",
            trigger: ".o_web_studio_form_view_editor .o_field_widget[name='website']",
            run() {
                const countFields = document.querySelectorAll(".o_web_studio_form_view_editor .o_field_widget[name]").length;
                if (!countFields === 2) {
                    throw new Error("There should be 2 fields in the form view")
                }
            }
        }
    ]
);

tour.register(
    "test_element_group_in_sidebar",
    {
        test: true,
        sequence: 260,
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']",
        },
        {
            trigger: ".o_form_view .o_form_editable",
        },
        {
            trigger: ".o_web_studio_navbar_item a",
        },
        {
            extra_trigger: ".o_web_studio_form_view_editor .o_field_widget[name='display_name']",
            trigger: ".o_web_studio_form_view_editor .o_field_widget[name='display_name']",
        },
        {
            trigger: ".o_field_many2manytags[name='groups'] .badge",
            run() {
                const tag = document.querySelector(".o_field_many2manytags[name='groups'] .badge");
                if (!tag || !tag.textContent.includes("Test Group")) {
                    throw new Error("The groups should be displayed in the sidebar");
                }
            },
        },
    ]
);

tour.register(
    "web_studio_custom_selection_field_edit_values",
    {
        test: true,
        sequence: 260
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            extra_trigger: ".o_form_view",
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_new_fields .o_web_studio_field_selection",
            run: "drag_and_drop (.o_web_studio_hook:eq(0))"
        },
        {
            trigger: ".o_web_studio_selection_new_value input",
            run: "text some value",
        },
        {
            trigger: ".modal-footer .btn-primary"
        },
        {
            trigger: ".o_web_studio_leave"
        },
        {
            extra_trigger: ".o_form_view",
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_form_view_editor .o_field_selection"
        },
        {
            trigger: ".o_web_studio_edit_selection_values"
        },
        {
            trigger: ".o_web_studio_selection_new_value input:last",
            run: "text another value"
        },
        {
            trigger: ".modal-footer .btn-primary"
        },
        {
            trigger: ".o_web_studio_leave"
        },
    ]
);


tour.register(
    "web_studio_test_enter_x2many_edition_with_multiple_subviews",
    {
        test: true,
        sequence: 260
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            extra_trigger: ".o_form_view span:contains('Address Type')",
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_form_view_editor .o_field_widget[name='child_ids'] .o_field_x2many_list",
            extra_trigger: ".o_list_renderer span:contains('Address Type')"
        },
        {
            extra_trigger: ".o-web-studio-edit-x2manys-buttons",
            trigger: ".o_web_studio_editX2Many[data-type='list']"
        },
        {
            trigger: ".o_content > .o_list_renderer span:contains('Address Type')"
        }
    ]
);

tour.register(
    "web_studio_test_enter_x2many_edition_with_multiple_subviews_correct_xpath",
    {
        test: true,
        sequence: 260,
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
        },
        {
            extra_trigger: ".o_form_view",
            trigger: ".o_web_studio_navbar_item a"
        },
        {
            trigger: ".o_web_studio_form_view_editor .o_field_widget[name='child_ids'] .o_field_x2many_list",
        },
        {
            extra_trigger: ".o-web-studio-edit-x2manys-buttons",
            trigger: ".o_web_studio_editX2Many[data-type='list']"
        },
        {
            extra_trigger: ".o_web_studio_breadcrumb .breadcrumb-item:contains('Subview List')",
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_header"
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component[title='Active']",
            run: "drag_and_drop (.o_web_studio_hook:eq(0))"
        },
        {
            content: "Check that the active field has been added",
            trigger: ".o_web_studio_view_renderer .o_list_view thead th[data-name='active']"
        }
    ]
)

tour.register("web_studio_test_studio_view_is_last",
    {
        test: true,
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']",
        },
        {
            extra_trigger: ".o_form_view",
            trigger: ".o_web_studio_navbar_item a",
        },
        {
            trigger: ".o_web_studio_sidebar .o_web_studio_existing_fields_header",
        },
        {
            extra_trigger: ".o_web_studio_existing_fields_section:not(.d-none)",
            trigger:
                ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component:contains(Website Link)",
            run() {
                $(
                    ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component:contains(Website Link)"
                )[0].scrollIntoView();
            },
        },
        {
            trigger:
                ".o_web_studio_sidebar .o_web_studio_existing_fields_section .o_web_studio_component:contains(Website Link)",
            run: "drag_and_drop_native (.o_web_studio_form_view_editor .o_inner_group .o_web_studio_hook:last)",
        },
        {
            trigger: ".o_web_studio_form_view_editor .o_field_widget[name='website']",
            allowInvisible: true,
            run() {},
        },
    ],
);

tour.register("web_studio_test_edit_form_subview_attributes",
    {
        test: true,
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']",
        },
        {
            extra_trigger: ".o_form_view",
            trigger: ".o_web_studio_navbar_item a",
        },
        {
            trigger:
                ".o_web_studio_form_view_editor .o_field_widget[name='child_ids'] .o_field_x2many_list",
        },
        {
            extra_trigger: ".o-web-studio-edit-x2manys-buttons",
            trigger: ".o_web_studio_editX2Many[data-type='form']",
        },
        {
            extra_trigger: ".o_web_studio_breadcrumb .breadcrumb-item:contains(Subview Form)",
            trigger: ".o_web_studio_sidebar .o_web_studio_view",
        },
        {
            trigger: ".o_web_studio_sidebar input[name='create']:checked",
        },
        {
            trigger: ".o_web_studio_sidebar input[name='create']:not(:checked)",
            run() {},
        },
    ]
);

tour.register("web_studio_test_move_similar_field",
    {
        test: true,
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']",
        },
        {
            extra_trigger: ".o_form_view",
            trigger: ".o_web_studio_navbar_item a",
        },
        {
            extra_trigger: ".o_web_studio_form_view_editor",
            trigger: ".o_notebook_headers .nav-item:eq(1) a",
        },
        {
            trigger: ".tab-pane.active [data-field-name=display_name]",
            run: "drag_and_drop_native (.o_web_studio_form_view_editor .o_web_studio_hook:eq(1))",
        },
        {
            trigger: ".o_web_studio_leave",
            run() {
            },
        },
    ]
);

tour.register("web_studio_test_related_file",
    {
        test: true,
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_user_menu']",
        },
        {
            content: "second",
            extra_trigger: ".o_form_view",
            trigger: ".o_web_studio_navbar_item a",
        },
        {
            extra_trigger: ".o_web_studio_form_view_editor",
            trigger: ".o_web_studio_field_related",
            run: "drag_and_drop (.o_inner_group)",
        },
        {
            extra_trigger: ".o_web_studio_field_modal",
            trigger: ".o_field_selector_value",
            run() {
                $('.o_field_selector_value').focusin();
            },
        },
        {
            extra_trigger: ".o_field_selector_popover:not(.d-none)",
            trigger: ".o_field_selector_search input",
            run: "text Related Partner",
        },
        {
            trigger: ".o_field_selector_item:contains(Related Partner)",
        },
        {
            trigger: ".o_field_selector_value",
        },
        {
            extra_trigger: ".o_field_selector_popover:not(.d-none)",
            trigger: ".o_field_selector_search input",
            run: "text New File",
        },
        {
            trigger: ".o_field_selector_item:contains(New File)",
        },
        {
            trigger: ".modal-footer .btn-primary:first",
        },
        {
            trigger: ".o_web_studio_leave",
            run() { },
        },
    ]
);


tour.register(
    "web_studio_test_remove_column_invisible_when_setting_invisible_domain",
    {
        test: true,
    },
    [
        {
            trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']",
        },
        {
            extra_trigger: ".o_list_view",
            trigger: ".o_web_studio_navbar_item a",
        },
        {
            extra_trigger: ".o_web_studio_list_view_editor",
            trigger: ".o_web_studio_view",
        },
        {
            trigger: "#show_invisible"
        },
        {
            trigger: "th[data-name=user_id]"
        },
        {
            trigger: ".o_web_studio_attrs[data-type=invisible]",
        },
        {
            trigger: ".o_domain_add_first_node_button",
        },
        {
            trigger: ".modal-footer .btn-primary"
        },
        {
            trigger: ".o_web_studio_leave",
            run() {},
        },
    ]
);
