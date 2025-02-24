/** @odoo-module **/

import { SearchModel } from "@web/search/search_model";
import { Domain } from "@web/core/domain";

export class AppointmentSearchModel extends SearchModel {
    /*
    * Overwrite to introduce calendarDomain
    */
    setup(services) {
        this.calendarDomain = [];
        super.setup(...arguments);
    }
    /*
    * Overwrite to add our jsTree
    * Regretfully, none of child method can be triggered, so we have to redefine the whole return
    */
    _getDomain(params = {}) {
        var domain =  super._getDomain(...arguments);        
        try {
            domain = Domain.and([domain, this.calendarDomain]);
            return params.raw
                ? domain
                : domain.toList(Object.assign({}, this.globalContext, this.userService.context));
        } catch (error) {
            throw new Error(
                `${this.env._t("Failed to evaluate the domain")} ${domain.toString()}.\n${
                    error.message
                }`
            );
        };
    }
    /*
    * The method to save received jsTree domain
    */
    toggleCalendarDomain(filtersDomain, filtersContext) {
        this.calendarDomain = filtersDomain;
        Object.assign(this.globalContext, filtersContext);
        this._notify();
    }
}
