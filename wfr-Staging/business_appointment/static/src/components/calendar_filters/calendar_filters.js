/** @odoo-module **/

import { getColor } from "@web/views/calendar/colors";
import { Domain } from "@web/core/domain";
import { _lt } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted, onWillStart, useState } = owl;

export class CalendarFilters extends Component {
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            resourceTypes: [],
            states: [],
            activeResourceType: null,
            activeResources: [],
            activeService: null,
            activeStates: [],
        });
        onWillStart(async () => {
            await this._loadFilters(this.props);
        });
        onMounted(() => {
            this._reloadSearch();
        });
    }
    /*
    * The getter method for available resources
    */
    get availableResources() {
        if (this.state.activeResourceType) {
            return this.state.activeResourceType.resources || [];
        }
        return []
    }
    /*
    * The getter method for available services
    */
    get availableServices() {
        if (this.state.activeResources && this.state.activeResources.length != 0) {
            const allServices = [].concat(...this.state.activeResources.map(rec => rec.services));
            return [...new Map(allServices.map((service) => [service["id"], service])).values()]
        }
        else if (this.state.activeResourceType) {
            return this.state.activeResourceType.services || [];
        }
        return []
    }
    /*
    * Getter for domain
    */
    get filtersDomain() {
        var filtersDomain = [];
        if (this.activeResourcesIds && this.activeResourcesIds.length != 0) {
            var resourceDomain = [];
            _.each(this.activeResourcesIds, function (activeResource) {
                resourceDomain = Domain.or([resourceDomain, [["extra_resource_ids", "=", activeResource]]])
            })
            resourceDomain = Domain.or([resourceDomain, [["resource_id", "in", this.activeResourcesIds]]]);
            resourceDomain = Domain.or([resourceDomain, [["info_resource_id", "in", this.activeResourcesIds]]]);
            filtersDomain = Domain.and([filtersDomain, resourceDomain])
        }
        else if (this.activeResourcesTypeId) {
            // filter by resource type only if resources are not selected, since they might belong to a different type
            filtersDomain = Domain.and([filtersDomain, [["resource_id.resource_type_id", "=", this.activeResourcesTypeId]]])
        };
        if (this.activeServiceId) {
            filtersDomain = Domain.and([filtersDomain, [["service_id", "=", this.activeServiceId]]])
        };
        if (this.activeStatesIds && this.activeStatesIds.length != 0) {
            filtersDomain = Domain.and([filtersDomain, [["state", "in", this.activeStatesIds]]])
        };
        return filtersDomain
    }
    /*
    * Getter for context
    * Important: here we do not for empty values, since otherwise once selected resource will in context until a new
    * one is chosen
    */
    get filtersContext() {
        return {
            default_resource_type_id: this.activeResourcesTypeId,
            default_resource_id: this.activeResourcesIds,
            default_service_id: this.activeServiceId,
            default_state: this.activeStatesIds,
        };
    }
    /*
    * The getter method to get id of the active resource type
    */
    get activeResourcesTypeId() {
        return this.state.activeResourceType ? this.state.activeResourceType.id : false
    }
    /*
    * The getter method to get ids of active resources
    */
    get activeResourcesIds() {
        return this.state.activeResources ? this.state.activeResources.map(rec => rec.id) : []
    }
    /*
    * The getter method to get id of the active serice
    */
    get activeServiceId() {
        return this.state.activeService ? this.state.activeService.id : false
    }
    /*
    * The getter method to get the list of actively chosen states
    */
    get activeStatesIds() {
        return this.state.activeStates ? this.state.activeStates.map(rec => rec[0]) : []
    }
    /*
    * The method to prepare the inital values for the filters
    */
    async _loadFilters(props) {
        const availableFilters = await this.orm.call(
            "business.resource.type",
            "action_return_types_and_resources",
            [],
            { context: this.env.searchModel.globalContext },
        );
        Object.assign(this.state, {
            "resourceTypes": availableFilters.resource_types,
            "appointmentStates": availableFilters.states,
        });
        var activeResourceType = availableFilters.active_resource_type_id;
        if (!activeResourceType) {
            activeResourceType = availableFilters.resource_types.length !=0 ? availableFilters.resource_types[0].id : null;
        };
        if (activeResourceType) {
            await this._onSelectResourceType(activeResourceType, true);
            if (availableFilters.active_resource_id && availableFilters.active_resource_id.length != 0) {
                for (const activeResource of availableFilters.active_resource_id) {
                    await this._onSelectResource(activeResource, true);
                };
            };
            if (availableFilters.active_service_id) {
                await this._onSelectService(availableFilters.active_service_id, true);
            }
            if (availableFilters.active_state && availableFilters.active_state.length != 0) {
                for (const activeState of availableFilters.active_state) {
                    await this._onSelectState(activeState, true);
                };
            }
        };
    }
    /*
    * The method to notify changes to the model
    */
    async _reloadSearch(noreload=false) {
        if (!noreload) {
            this.env.searchModel.toggleCalendarDomain(this.filtersDomain, this.filtersContext);
        };
    }
    /*
    * The method to process resource type selection
    */
    async _onSelectResourceType(resourceTypeId, noreload=false) {
        const chosenResourceTypes = this.state.resourceTypes.filter(rec => rec.id == resourceTypeId);
        const chosenResourceType = chosenResourceTypes.length != 0 ? chosenResourceTypes[0] : false;
        Object.assign(this.state, { activeResources: [], activeResourceType: chosenResourceType});
        if (!this._isActiveServiceAvailable()) {
            this.state.activeService = false;
        };
        await this._reloadSearch(noreload);
    }
    /*
    * The method to process resource selection
    */
    async _onSelectResource(resourceId, noreload=false) {
        var activeResources = [];
        if (this.activeResourcesIds.includes(resourceId)) {
            activeResources = this.state.activeResources.filter(rec => rec.id != resourceId)
        }
        else {
            const chosenResources = this.availableResources.filter(rec => rec.id == resourceId);
            activeResources = chosenResources.concat(this.state.activeResources)
        };
        Object.assign(this.state, { activeResources: activeResources });
        if (!this._isActiveServiceAvailable()) {
            this.state.activeService = false;
        };
        await this._reloadSearch(noreload);
    }
    /*
    * The method to select all found resources
    */
    async onSelectAllResources() {
        Object.assign(this.state, { activeResources: this.availableResources });
        await this._reloadSearch();
    }
    /*
    * The method to clear resources selection
    */
    async onClearAllResources() {
        Object.assign(this.state, { activeResources: [] });
        await this._reloadSearch();
    }
    /*
    * The method to process service selection
    */
    async _onSelectService(serviceId, noreload=false) {
        const chosenServices = await this.availableServices.filter(rec => rec.id == serviceId);
        const chosenService = chosenServices.length != 0 ? chosenServices[0] : false;
        Object.assign(this.state, { activeService: chosenService});
        await this._reloadSearch(noreload);
    }
    /*
    * The method to process state selection
    */
    async _onSelectState(appointmentState, noreload=false) {
        var activeStates = [];
        if (this.activeStatesIds.includes(appointmentState)) {
            activeStates = this.state.activeStates.filter(rec => rec[0] != appointmentState);
        }
        else {
            const chosenStates = this.state.appointmentStates.filter(rec => rec[0] == appointmentState);
            activeStates = chosenStates.concat(this.state.activeStates);
        };
        Object.assign(this.state, { activeStates: activeStates });
        await this._reloadSearch(noreload);
    }
    /*
    * The method to select all found states
    */
    async onSelectAllStates() {
        Object.assign(this.state, { activeStates: this.state.appointmentStates });
        await this._reloadSearch();
    }
    /*
    * The method to clear states selection
    */
    async onClearAllStates() {
        Object.assign(this.state, { activeStates: [] });
        await this._reloadSearch();
    }
    /*
    * The method to save currently selected filters as default
    */
    async _onSaveDefaults() {
        const defaultValues = {
            "active_resource_type_id": this.activeResourcesTypeId,
            "active_resource_id": this.activeResourcesIds,
            "active_service_id": this.activeServiceId,
            "active_state": this.activeStatesIds,
        }
        await this.orm.call("res.partner", "action_save_ba_calendar_defaults", [defaultValues]);
    }
    /*
    * The method to define whether the active service is available after the update
    */
    _isActiveServiceAvailable() {
        if (this.availableServices.map(rec => rec.id).includes(this.activeServiceId)) {
            return true
        }
        return false
    }
    /*
    * The method to get color based on the record id
    */
    getColor(key) {
        return getColor(key)
    }
};

CalendarFilters.template = "business_appointment.CalendarFilters";
