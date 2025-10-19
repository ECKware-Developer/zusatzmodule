/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

const BANNER = "[pos_deposit_auto v18.0.4.1 alias]";
console.info(BANNER, "loaded");

function getLineQty(line) {
    return typeof line.get_quantity === "function" ? line.get_quantity() : line.quantity;
}

patch(PosStore.prototype, {
    async addLineToOrder(vals, order = this.get_order(), opts = {}, configure = true) {
        const line = await super.addLineToOrder(vals, order, opts, configure);
        try {
            if (!line || !order) return line;
            const product = line.product || (typeof line.get_product === "function" ? line.get_product() : null);
            if (!product || line.is_deposit) return line;

            const depId = product.pda_deposit_product_id;
            const factor = Number(product.pda_deposit_factor || 1);
            if (!depId || depId === product.id) return line;

            const qty = (getLineQty(line) || 1) * (isFinite(factor) && factor > 0 ? factor : 1);
            const depLine = await super.addLineToOrder({ productId: depId, qty }, order, {}, false);
            if (depLine) {
                depLine.is_deposit = true;
                depLine.linked_line_uid = line.uid;
                line.linked_deposit_uid = depLine.uid;
            }
        } catch (e) {
            console.error(BANNER, "error in addLineToOrder:", e);
        }
        return line;
    },
});