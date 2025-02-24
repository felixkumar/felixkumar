odoo.define('website_helpdesk.form', function (require) {
'use strict';

var core = require('web.core');
var FormEditorRegistry = require('website.form_editor_registry');

const _lt = core._lt;

FormEditorRegistry.add('create_ticket', {
    formFields: [{
        type: 'char',
        required: true,
        name: 'partner_name',
        fillWith: 'name',
        string: _lt('Your Name'),
    }, {
        type: 'email',
        required: true,
        name: 'partner_email',
        fillWith: 'email',
        string: _lt('Your Email'),
    }, {
        type: 'char',
        modelRequired: true,
        name: 'name',
        string: _lt('Subject'),
    }, {
        type: 'char',
        name: 'description',
        string: _lt('Description'),
    }, {
        type: 'binary',
        custom: true,
        name: _lt('Attachment'),
    }],
    fields: [{
        name: 'team_id',
        type: 'many2one',
        relation: 'helpdesk.team',
        string: _lt('Helpdesk Team'),
    }],
    successPage: '/your-ticket-has-been-submitted',
});

});
