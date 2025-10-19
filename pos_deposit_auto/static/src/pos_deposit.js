/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "point_of_sale/app/store/pos_store";
import { Order } from "point_of_sale/app/models/order";
import { Orderline } from "point_of_sale/app/models/line";

/**
 * Helpers
 */
function getDepositProductId(product) {
    // Accept number or m2o tuple [id, name]
    const v = product && product.deposit_product_id;
    if (!v) return null;
    if (Array.isArray(v)) return v[0];
    if (typeof v === "number") return v;
    if (typeof v === "object" && v.id) return v.id;
    return null;
}

function getDepositFactor(product) {
    // Optional studio/custom field; default to 1
    const v = product && product.x_deposit_factor;
    const f = (v === 0 || v) ? Number(v) : 1;
    return isFinite(f) && f > 0 ? f : 1;
}

function getLineQuantity(line) {
    // Compatible with different POS builds
    if (typeof line.get_quantity === "function") {
        return line.get_quantity();
    }
    return line.quantity;
}

/**
 * 1) Auto-create deposit line after a main product line is added.
 */
patch(PosStore.prototype, {
    async addLineToOrder(vals, order = this.get_order(), opts = {}, configure = true) {
        const line = await super.addLineToOrder(vals, order, opts, configure);
        try {
            if (!line || !order) return line;
            const product = line.product || (typeof line.get_product === "function" ? line.get_product() : null);
            if (!product) return line;

            const depProductId = getDepositProductId(product);
            if (!depProductId) return line;                   // no deposit configured

            // Avoid loops if someone accidentally points deposit product to itself
            if (product.id === depProductId) return line;

            // Do not create deposit line for lines that are *already* a deposit
            if (line.is_deposit) return line;

            // Quantity * factor (e.g., case with 20 bottles)
            const factor = getDepositFactor(product);
            const qty = getLineQuantity(line) * factor;

            // Create the deposit line using the product id; price comes from product data.
            const depLine = await super.addLineToOrder(
                { productId: depProductId, qty },
                order,
                {},    // keep default price
                false  // no further configuration
            );
            if (depLine) {
                depLine.is_deposit = true;
                depLine.linked_line_uid = line.uid;
                line.linked_deposit_uid = depLine.uid;
            }
        } catch (e) {
            console.warn("[pos_deposit_auto] Failed to add deposit line:", e);
        }
        return line;
    },
});

/**
 * 2) Keep quantities in sync between main line and deposit line.
 */
patch(Orderline.prototype, {
    set_quantity(qty, keep_price) {
        const res = super.set_quantity(qty, keep_price);
        try {
            const order = this.order;
            if (!order) return res;

            // If this is a main line with a linked deposit, update deposit qty
            if (this.linked_deposit_uid) {
                const dep = order.get_orderlines().find((l) => l.uid === this.linked_deposit_uid);
                if (dep) {
                    const product = this.product || (typeof this.get_product === "function" ? this.get_product() : null);
                    const factor = getDepositFactor(product || {});
                    const newQty = getLineQuantity(this) * factor;
                    // Call super on dep line to avoid recursion guard
                    Orderline.prototype.set_quantity.call(dep, newQty, keep_price);
                }
            }

            // If this is a deposit line, enforce sync from its main line
            if (this.is_deposit && this.linked_line_uid) {
                const main = order.get_orderlines().find((l) => l.uid === this.linked_line_uid);
                if (main) {
                    const product = main.product || (typeof main.get_product === "function" ? main.get_product() : null);
                    const factor = getDepositFactor(product || {});
                    const newQty = getLineQuantity(main) * factor;
                    super.set_quantity(newQty, keep_price);
                }
            }
        } catch (e) {
            console.warn("[pos_deposit_auto] Sync qty error:", e);
        }
        return res;
    },
});

/**
 * 3) Remove deposit line if main line is removed; if deposit is removed, unlink its main line.
 */
patch(Order.prototype, {
    removeOrderline(line) {
        // Capture links before removal
        const isDeposit = line && line.is_deposit;
        const linkedUid = line && (line.linked_line_uid || line.linked_deposit_uid);
        const res = super.removeOrderline(line);
        try {
            if (!linkedUid) return res;
            const other = this.get_orderlines().find((l) => l.uid === linkedUid);
            if (!other) return res;
            // If we removed main -> remove deposit as well
            if (!isDeposit && other.is_deposit) {
                super.removeOrderline(other);
            }
            // If we removed deposit -> unlink on main
            if (isDeposit && other) {
                delete other.linked_deposit_uid;
            }
        } catch (e) {
            console.warn("[pos_deposit_auto] Remove link error:", e);
        }
        return res;
    },
});