/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { _lt } from "@web/core/l10n/translation";
import { renderToMarkup } from "@web/core/utils/render";
import { Record, RelationalModel } from "@web/views/basic_relational_model";
import { patch } from "@web/core/utils/patch";

import {
    xml,
    reactive,
    useComponent,
    useEnv,
    toRaw,
    onMounted,
    onWillDestroy,
    onWillUpdateProps,
} from "@odoo/owl";

patch(RelationalModel.prototype, "studio.approval", {
    setup() {
        this._super.apply(this, arguments);
        this.studioHooks = {
            onRecordSaved: () => {},
        };
    },
});

patch(Record.prototype, "studio.approval", {
    async save() {
        const res = await this._super.apply(this, arguments);
        this.model.studioHooks.onRecordSaved();
        return res;
    },
});

const missingApprovalsTemplate = xml`
    <ul>
        <li t-foreach="missingApprovals" t-as="approval" t-key="approval_index">
            <t t-esc="approval.message or approval.group_id[1]" />
        </li>
    </ul>
`;
const notificationTitle = _lt("The following approvals are missing:");

function getMissingApprovals(entries, rules) {
    const missingApprovals = [];
    const doneApprovals = entries.filter((e) => e.approved).map((e) => e.rule_id[0]);
    rules.forEach((r) => {
        if (!doneApprovals.includes(r.id)) {
            missingApprovals.push(r);
        }
    });
    return missingApprovals;
}

class StudioApproval {
    constructor() {
        this._data = reactive({});

        // Lazy properties to be set by specialization.
        this.orm = null;
        this.studio = null;
        this.notification = null;
        this.resModel = null;
        this.resId = null;
        this.method = null;
        this.action = null;
    }

    get dataKey() {
        return `${this.resModel}-${this.resId}-${this.method}-${this.action}`;
    }

    /**
     * The approval's values for a given resModel, resId, method and action.
     * If current values don't exist, we fetch them from the server. Owl's fine reactivity
     * does the update of every component using that state.
     */
    get state() {
        const state = this._getState();
        if (state.rules === null && !state.syncing && !this.willCheck) {
            this.fetchApprovals();
        }
        return state;
    }

    get inStudio() {
        return !!this.studio.mode;
    }

    displayNotification(data) {
        const missingApprovals = getMissingApprovals(data.entries, data.rules);
        this.notification.add(renderToMarkup(missingApprovalsTemplate, { missingApprovals }), {
            type: "warning",
            title: notificationTitle,
        });
    }

    async checkApproval() {
        const args = [this.resModel, this.resId, this.method, this.action];
        const state = this._getState();
        state.syncing = true;
        const result = await this.orm.call("studio.approval.rule", "check_approval", args);
        const approved = result.approved;
        if (!approved) {
            this.displayNotification(result);
        }
        this.willCheck = false;
        this.fetchApprovals(); // don't wait
        return approved;
    }

    async fetchApprovals() {
        const args = [this.resModel, this.method, this.action];
        const kwargs = {
            res_id: !this.studio.mode && this.resId,
        };

        const state = this._getState();
        state.syncing = true;
        try {
            const spec = await this.orm.silent.call(
                "studio.approval.rule",
                "get_approval_spec",
                args,
                kwargs
            );
            Object.assign(state, spec);
        } finally {
            state.syncing = false;
        }
    }

    /**
     * Create or update an approval entry for a specified rule server-side.
     * @param {Number} ruleId
     * @param {Boolean} approved
     */
    async setApproval(ruleId, approved) {
        try {
            await this.orm.call("studio.approval.rule", "set_approval", [[ruleId]], {
                res_id: this.resId,
                approved,
            });
        } finally {
            await this.fetchApprovals();
        }
    }

    /**
     * Delete an approval entry for a given rule server-side.
     * @param {Number} ruleId
     */
    async cancelApproval(ruleId) {
        try {
            await this.orm.call("studio.approval.rule", "delete_approval", [[ruleId]], {
                res_id: this.resId,
            });
        } finally {
            await this.fetchApprovals();
        }
    }

    _getState() {
        if (!(this.dataKey in this._data)) {
            this._data[this.dataKey] = { rules: null };
        }
        return this._data[this.dataKey];
    }
}

const approvalMap = new WeakMap();

export function useApproval({ getRecord, method, action }) {
    /* The component using this hook can be destroyed before ever being mounted.
    In practice, we do an rpc call in the component setup without knowing if it will be mounted.
    When a new instance of the component is created, it will share the same data, and the
    promise from `useService("orm")` will never resolve due to the old instance being destroyed.
    What we can do to prevent that, is initially use an unprotected orm and once
    the component has been mounted, we can switch the orm to the one from useService. */
    const protectedOrm = useService("orm");
    const unprotectedOrm = useEnv().services.orm;
    const studio = useService("studio");
    const notification = useService("notification");
    let record = getRecord(useComponent().props);
    const model = toRaw(record.model);
    let approvalModelCache = approvalMap.get(model);
    if (!approvalModelCache) {
        approvalModelCache = {
            approval: new StudioApproval(),
            onRecordSaved: new Map(),
        };
        approvalMap.set(model, approvalModelCache);
        const onRecordSaved = model.studioHooks.onRecordSaved;
        model.studioHooks.onRecordSaved = (...args) => {
            approvalModelCache.onRecordSaved.forEach((fn) => fn(args[0]));
            return onRecordSaved(...args);
        };
    }

    const specialize = {
        resModel: record.resModel,
        resId: record.resId,
        method,
        action,
        orm: unprotectedOrm,
        studio,
        notification,
    };

    const approval = reactive(
        Object.assign(Object.create(approvalModelCache.approval), specialize)
    );

    approvalModelCache.onRecordSaved.set(toRaw(approval), () => {
        if (!approval.resId && record.resId) {
            approval.resId = record.resId;
        } else {
            delete approval._data[approval.dataKey];
        }
    });
    onWillDestroy(() => approvalModelCache.onRecordSaved.delete(toRaw(approval)));
    onWillUpdateProps((nextProps) => {
        const nextRecord = getRecord(nextProps);
        approval.resId = nextRecord.resId;
        approval.resModel = nextRecord.resModel;
        record = nextRecord;
    });

    onMounted(() => {
        approval.orm = protectedOrm;
    });

    return approval;
}
