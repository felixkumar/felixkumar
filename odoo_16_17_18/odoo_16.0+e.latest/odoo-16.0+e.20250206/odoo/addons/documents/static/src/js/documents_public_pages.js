/** @odoo-module **/

import "web.dom_ready";

// The purpose of this module is to adapt the image preview size on the public
// page of shared documents

document.querySelectorAll('form[action*="/document/upload/"]').forEach(form => { 
    const input_csrf = document.createElement('input'); 
    input_csrf.type = 'hidden'; 
    input_csrf.name = 'csrf_token'; 
    input_csrf.value = odoo['csrf_token']; 
    form.prepend(input_csrf); 
});

const container = document.querySelector('#wrap .o_docs_single_container.o_has_preview');
if (container) {
    initPublicPages(container);
}

function initPublicPages(container) {
    const parent = container.parentElement;
    const image = container.querySelector('img');
    const actions = container.querySelector('.o_docs_single_actions');

    const checkResize = _.throttle(() => {
        image.style.maxHeight = parent.clientHeight - actions.offsetHeight;
    }, 100);

    image.addEventListener('load', () => {
        checkResize();
        image.style.opacity = 1;
        container.querySelector('.o_loading_img').remove();
    });

    window.addEventListener('resize', checkResize, false);
}
