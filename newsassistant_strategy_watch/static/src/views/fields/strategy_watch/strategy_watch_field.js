/** @odoo-module **/

import { BooleanFavoriteField } from "@web/views/fields/boolean_favorite/boolean_favorite_field";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

class StrategyWatchField extends BooleanFavoriteField {
    get label() {
        return this.props.record.data[this.props.name]
            ? _t("Remove from Strategy Watch")
            : _t("Add to Strategy Watch");
    }
}

export const strategyWatchField = {
    component: StrategyWatchField,
    displayName: _t("Strategy Watch"),
    supportedTypes: ["boolean"],
    isEmpty: () => false,
    extractProps: ({ attrs }, dynamicInfo) => ({
        noLabel: Boolean(attrs.nolabel),
        autosave: true,
        readonly: dynamicInfo.readonly,
    }),
};

registry.category("fields").add("strategy_watch", strategyWatchField);