/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "point_of_sale/app/store/pos_store";
import { Order } from "point_of_sale/app/models/order";
import { Orderline } from "point_of_sale/app/models/line";

const SYNC_FLAG = "__deposit_sync_in_progress__";

/** m2o helper: number, [id, name], or object with id */
function m2oId(val) {
    if (!val) return null;
    if (typeof val === "number") return val;
    if (Array.isArray(val)) return val[0];
    if (typeof val === "object" && val.id) return val.id;
    return null;
}

function getProductById(pos, id) {
    if (!id) return null;
    if (pos?.productIdToProduct?.[id]) return pos.productIdToProduct[id];
    if (pos?.db?.product_by_id?.[id]) return pos.db.product_by_id[id];
    const list = pos?.models?.["product.product"]?.data || [];
    for (const p of list) if (p.id === id) return p;
    return null;
}

/**
 * Resolve deposit product:
 * 1) product.x_deposit_product_1
 * 2) product.x_unit_sale_product -> its x_deposit_product_1
 * 3) fallbacks deposit_product_id / x_deposit_product_id
 */
function resolveDepositProductId(pos, product) {
    const direct = m2oId(product?.x_deposit_product_1);
    if (direct) return direct;
    const unitId = m2oId(product?.x_unit_sale_product);
    if (unitId) {
        const unitProd = getProductById(pos, unitId);
        const nested = m2oId(unitProd?.x_deposit_product_1);
        if (nested) return nested;
        const nestedFallback = m2oId(unitProd?.deposit_product_id) || m2oId(unitProd?.x_deposit_product_id);
        if (nestedFallback) return nestedFallback;
    }
    return m2oId(product?.deposit_product_id) || m2oId(product?.x_deposit_product_id) || null;
}

/** Resolve deposit factor (qty multiplier) */
function resolveDepositFactor(pos, product) {
    const q = Number(product?.x_quantity_by_deposit_product);
    if (isFinite(q) && q > 0) return q;
    const f = Number(product?.x_deposit_factor);
    if (isFinite(f) && f > 0) return f;
    const unitId = m2oId(product?.x_unit_sale_product);
    if (unitId) {
        const unitProd = getProductById(pos, unitId);
        const uq = Number(unitProd?.x_quantity_by_deposit_product);
        if (isFinite(uq) && uq > 0) return uq;
        const uf = Number(unitProd?.x_deposit_factor);
        if (isFinite(uf) && uf > 0) return uf;
    }
    return 1;
}

function getLineQty(line) {
    return typeof line.get_quantity === "function" ? line.get_quantity() : line.quantity;
}

/** Patch 1: add deposit line after adding a main product line */
patch(PosStore.prototype, {
    async addLineToOrder(vals, order = this.get_order(), opts = {}, configure = true) {
        const line = await super.addLineToOrder(vals, order, opts, configure);
        try {
            if (!line || !order) return line;
            const product = line.product || (typeof line.get_product === "function" ? line.get_product() : null);
            if (!product || line.is_deposit) return line;

            const depProdId = resolveDepositProductId(this, product);
            if (!depProdId || depProdId === product.id) return line;
            const depProd = getProductById(this, depProdId);
            if (!depProd) return line;

            const factor = resolveDepositFactor(this, product);
            const qty = getLineQty(line) * factor;

            // Guard against recursive sync
            order[SYNC_FLAG] = true;
            const depLine = await super.addLineToOrder({ productId: depProd.id, qty }, order, {}, false);
            order[SYNC_FLAG] = false;

            if (depLine) {
                depLine.is_deposit = true;
                depLine.linked_line_uid = line.uid;
                line.linked_deposit_uid = depLine.uid;
            }
        } catch (e) {
            console.warn("[pos_deposit_auto] add deposit failed:", e);
            order[SYNC_FLAG] = false;
        }
        return line;
    },
});

/** Patch 2: keep quantities in sync (guarded) */
patch(Orderline.prototype, {
    set_quantity(qty, keep_price) {
        const order = this.order;
        const res = super.set_quantity(qty, keep_price);
        try {
            if (!order || order[SYNC_FLAG]) return res;

            if (this.linked_deposit_uid) {
                const dep = order.get_orderlines().find(l => l.uid === this.linked_deposit_uid);
                if (dep) {
                    const product = this.product || (typeof this.get_product === "function" ? this.get_product() : null);
                    const factor = resolveDepositFactor(order.pos || order?.env?.pos || this.pos, product || {});
                    const newQty = getLineQty(this) * factor;
                    order[SYNC_FLAG] = true;
                    super.set_quantity.call(dep, newQty, keep_price);
                    order[SYNC_FLAG] = false;
                }
            }

            if (this.is_deposit && this.linked_line_uid) {
                const main = order.get_orderlines().find(l => l.uid === this.linked_line_uid);
                if (main) {
                    const product = main.product || (typeof main.get_product === "function" ? main.get_product() : null);
                    const factor = resolveDepositFactor(order.pos || order?.env?.pos || this.pos, product || {});
                    const newQty = getLineQty(main) * factor;
                    order[SYNC_FLAG] = true;
                    super.set_quantity.call(this, newQty, keep_price);
                    order[SYNC_FLAG] = false;
                }
            }
        } catch (e) {
            console.warn("[pos_deposit_auto] qty sync error:", e);
            if (order) order[SYNC_FLAG] = false;
        }
        return res;
    },
});

/** Patch 3: linked remove behavior */
patch(Order.prototype, {
    removeOrderline(line) {
        const order = this;
        const isDeposit = line && line.is_deposit;
        const linkedUid = line && (line.linked_line_uid || line.linked_deposit_uid);
        const res = super.removeOrderline(line);
        try {
            if (!linkedUid) return res;
            const other = order.get_orderlines().find(l => l.uid === linkedUid);
            if (!other) return res;
            if (!isDeposit && other.is_deposit) {
                super.removeOrderline(other);
            }
            if (isDeposit && other) {
                delete other.linked_deposit_uid;
            }
        } catch (e) {
            console.warn("[pos_deposit_auto] remove link error:", e);
        }
        return res;
    },
});