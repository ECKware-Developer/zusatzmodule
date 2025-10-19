/** @odoo-module **/
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ClosePosPopup } from "@point_of_sale/app/screens/closing_popup/closing_popup";
import { _t } from "@web/core/l10n/translation";

const euro = (amount, symbol="€") => {
    const v = (Number(amount) || 0).toFixed(2);
    return `${v} ${symbol}`;
};

const localKey = (env) => `pos_closure_card_tips_session_${env.services.pos?.pos_session?.id || 'unknown'}`;

async function fetchConfigSettings(env) {
    const config_id = env.services.pos.configId;
    const result = await env.services.rpc(
        { model: "pos.config", method: "get_pos_ui_settings", args: [config_id] },
        { shadow: true }
    );
    return result || { closure_target_cash: 250.0, print_closure_auto: true, currency_symbol: "€" };
}

function computeFromOrders(pos) {
    const orders = pos.models?.order?.getAll?.() || pos.get_order_list?.() || [];
    const payment_methods = pos.payment_methods || [];
    const cashMethodIds = new Set(payment_methods.filter(pm => pm.type === 'cash').map(pm => pm.id));

    let amount_total = 0;
    let amount_cash_sales = 0;
    let amount_invoice = 0;
    let tips_cash = 0;

    for (const o of orders) {
        const json = o.export_as_JSON ? o.export_as_JSON() : o;
        if (o.get_total_with_tax) amount_total += o.get_total_with_tax();
        else if (json?.amount_total) amount_total += json.amount_total;

        const payments = o.get_paymentlines ? o.get_paymentlines() : (json.statement_ids || []).map((s) => s[2]);
        for (const p of payments) {
            const method_id = p.payment_method?.id || p.payment_method_id || p.journal_id;
            const is_tip = p.is_tip || p.is_tip_payment || false;
            const amount = p.amount || 0;

            if (cashMethodIds.has(method_id)) {
                if (is_tip) tips_cash += amount;
                else amount_cash_sales += amount;
            }
        }

        if (o.is_to_invoice?.() || json.to_invoice) {
            amount_invoice += o.get_total_with_tax ? o.get_total_with_tax() : (json.amount_total || 0);
        }
    }

    return { amount_total, amount_cash_sales, amount_invoice, tips_cash };
}

function getCashboxEnd(pos) {
    const session = pos.pos_session || {};
    const counted = session.cash_register_balance_end_real;
    if (typeof counted === 'number' && !isNaN(counted)) return counted;

    const start = session.cash_register_balance_start || session.opening_balance_cash || 0;
    const { amount_cash_sales } = computeFromOrders(pos);
    return start + amount_cash_sales;
}

async function makeReceiptData(env) {
    const pos = env.services.pos;
    const cfg = await fetchConfigSettings(env);
    const currency = cfg.currency_symbol || '€';

    const { amount_total, amount_cash_sales, amount_invoice, tips_cash } = computeFromOrders(pos);

    const cardTipsManual = Number(window.localStorage.getItem(localKey(env)) || '0');
    const tips_total = tips_cash + cardTipsManual;

    const ist_cash = getCashboxEnd(pos);
    const target = cfg.closure_target_cash || 0;
    const cash_to_withdraw = Math.max(0, ist_cash - target);

    const user = env.services.user;
    const company = env.services.company;

    return {
        company_name: company?.name || "",
        pos_name: pos?.config?.name || "",
        session_name: pos?.pos_session?.name || "",
        cashier_name: user?.name || "",
        datetime_str: new Date().toLocaleString(),
        amount_total_str: euro(amount_total, currency),
        amount_cash_sales_str: euro(amount_cash_sales, currency),
        amount_invoice_str: amount_invoice ? euro(amount_invoice, currency) : null,
        tips_cash_str: euro(tips_cash, currency),
        tips_card_manual_str: cardTipsManual ? euro(cardTipsManual, currency) : null,
        tips_total_str: euro(tips_total, currency),
        target_cash_str: euro(target, currency),
        cashbox_end_str: euro(ist_cash, currency),
        cash_to_withdraw_str: euro(cash_to_withdraw, currency),
    };
}

async function printClosureReceipt(env) {
    const qweb = env.services.qweb;
    const data = await makeReceiptData(env);
    const html = qweb.render("pos_closure_receipt.ClosureReceipt", { data });
    await env.services.pos.printHtml(html);
}

async function promptCardTips(env) {
    const current = Number(window.localStorage.getItem(localKey(env)) || '0');
    const { confirmed, payload } = await env.services.popup.add("NumberPopup", {
        title: _t("Kartentrinkgeld erfassen"),
        startingValue: current || 0,
        isInputSelected: true,
        body: _t("Bitte den Betrag der über das Kartenterminal erhaltenen Trinkgelder eingeben. Dieser Betrag wird auf dem Abschlussbon berücksichtigt und aus der Kasse auszuzahlen."),
        confirmText: _t("Speichern"),
    });
    if (confirmed) {
        const v = Number(payload);
        const safe = isFinite(v) && v >= 0 ? v : 0;
        window.localStorage.setItem(localKey(env), String(safe));
    }
}

patch(ClosePosPopup.prototype, "pos_closure_receipt.ClosePosPopup", {
    setup() {
        this._super(...arguments);
        this._closureSettingsPromise = fetchConfigSettings(this.env);
    },

    get extraButtons() {
        const buttons = this._super ? this._super(...arguments) : [];
        buttons.push({
            text: _t("Kartentrinkgeld erfassen"),
            class: "btn-secondary",
            close: false,
            click: async () => { await promptCardTips(this.env); },
        });
        buttons.push({
            text: _t("Abschlussbon drucken"),
            class: "btn-primary",
            close: false,
            click: async () => { await printClosureReceipt(this.env); },
        });
        return buttons;
    },

    async confirm() {
        const cfg = await this._closureSettingsPromise;
        if (cfg.print_closure_auto) {
            try { await printClosureReceipt(this.env); }
            catch (e) { console.warn("Abschlussbon: automatischer Druck fehlgeschlagen", e); }
        }
        await this._super(...arguments);
    },
});

registry.category("pos_screens");
