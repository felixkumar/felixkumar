/** @odoo-module */
import tour from 'web_tour.tour';

tour.register(
    "website_studio_new_form_page_collision_tour",
    {
        test: true,
    },
    [{
        // open Studio
        trigger: '.o_menu_systray .o_web_studio_navbar_item',
    }, {
        trigger: '.o_web_studio_new_app',
    }, {
        // the next steps are here to create a new app
        trigger: '.o_web_studio_app_creator_next',
    }, {
        //create 'webModule' app
        trigger: '.o_web_studio_app_creator_name > input',
        run: 'text webModule',
    }, {
        trigger: '.o_web_studio_app_creator_next.is_ready',
    }, {
        //name the module 'web', to check collision with already existing /web route
        trigger: '.o_web_studio_app_creator_menu > input',
        run: 'text web',
    }, {
        trigger: '.o_web_studio_app_creator_next.is_ready',
    }, {
        trigger: '.o_web_studio_model_configurator_next',
    }, {
        // switch to Website tab
        trigger: '.o_web_studio_menu .o_menu_sections li:contains(Website)',
        extra_trigger: '.o_web_studio_leave', /* wait to be inside studio */
        timeout: 60000, /* previous step reloads registry, etc. - could take a long time */
    }, {
        // click on "New Form"
        // it should create /web-form instead of /web to prevent collision
        trigger: '.o_website_studio_form .o_web_studio_thumbnail',
    }, {
        content: "Check that we are in edit mode",
        trigger: '.o_website_preview.editor_enable.editor_has_snippets',
        run: function () {
            const $iframe = this.$anchor.find('iframe.o_iframe:not(.o_ignore_in_tour)');
            const menuitems = Array.from($iframe.contents().find('#top_menu a[role="menuitem"]'))
                .map(x=> {
                    return {
                        href: x.getAttribute('href'),
                        name: x.textContent.trim()
                    }
                });
            if (!menuitems.some(x => x.href === '/web-form' && x.name === 'web Form')) {
                throw new Error('No /web-form menu item found');
            }
        },
    }]
);
