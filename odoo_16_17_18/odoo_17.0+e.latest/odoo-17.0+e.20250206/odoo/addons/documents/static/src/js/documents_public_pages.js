/** @odoo-module **/

import { whenReady } from "@odoo/owl";

whenReady().then(() => {
    document.querySelectorAll('form[action*="/document/upload/"]').forEach(form => {
        const input_csrf = document.createElement('input');
        input_csrf.type = 'hidden';
        input_csrf.name = 'csrf_token';
        input_csrf.value = odoo['csrf_token'];
        form.prepend(input_csrf);
    });
})
