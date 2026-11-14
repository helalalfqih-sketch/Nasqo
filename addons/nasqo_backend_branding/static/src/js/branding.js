/** @odoo-module **/
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { titleService } from "@web/core/browser/title_service";
import { Dialog } from "@web/core/dialog/dialog";
import {
    ErrorDialog, ClientErrorDialog, NetworkErrorDialog, RPCErrorDialog,
    WarningDialog, RedirectWarningDialog, odooExceptionTitleMap,
} from "@web/core/errors/error_dialogs";

const BRAND = "نسقو برو | NASQO PRO";

// Keep action titles and notification counters; add a persistent product name.
patch(titleService, {
    start(...args) {
        const service = super.start(...args);
        const setParts = service.setParts;
        service.setParts = (parts) => setParts({ ...parts, nasqo_brand: BRAND });
        service.setParts({});
        return service;
    },
});

const menu = registry.category("user_menuitems");
menu.remove("odoo_account");
menu.remove("support");
menu.add("nasqo_home", () => ({
    type: "item", id: "nasqo_home", description: "موقع نسقو برو",
    href: "/", callback: () => window.location.assign("/"), sequence: 20,
}));

patch(Dialog, { defaultProps: { ...Dialog.defaultProps, title: BRAND } });
patch(ErrorDialog, { title: "خطأ في نسقو برو" });
patch(ClientErrorDialog, { title: "خطأ في واجهة نسقو برو" });
patch(NetworkErrorDialog, { title: "تعذر الاتصال بنسقو برو" });
patch(RPCErrorDialog.prototype, {
    inferTitle() {
        super.inferTitle();
        if (!this.props.exceptionName || !odooExceptionTitleMap.has(this.props.exceptionName)) {
            this.title = {
                server: "خطأ في خادم نسقو برو",
                script: "خطأ في واجهة نسقو برو",
                network: "تعذر الاتصال بنسقو برو",
            }[this.props.type] || "خطأ في نسقو برو";
        }
    },
});
patch(WarningDialog.prototype, {
    inferTitle() {
        return this.props.title || "تنبيه نسقو برو";
    },
});
patch(RedirectWarningDialog.prototype, {
    setup() {
        super.setup();
        if (!this.props.subType) {
            this.title = "تنبيه نسقو برو";
        }
    },
});
