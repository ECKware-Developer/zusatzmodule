/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

/**
 * Small helper utilities
 */
const BANNER = "[pos_deposit_auto v18.0.3]";
console.info(BANNER, "loaded");

function m2oId(val) {
    if (!val) return null;
    if (typeof val === "number") return val;
    if (Array.isArray(val)) return val[0];
    if (typeof val === "object" && val.id) return val.id;
    return null;
}

function getProductById(pos, id) {
    if (!id) return null;
    const pmap = pos && (pos.productIdToProduct || pos.db?.product_by_id);
    if (pmap && pmap[id]) return pmap[id];
    const list = pos?.models?.["product.product"]?.data || [];
    for (const p of list) if (p.id === id) return p;
    return null;
}

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

/**
 * Patch PosStore.addLineToOrder:
 * - Auto-create a deposit line linked to the main line
 * - Keep a very light-weight sync: if user changes main qty immediately after adding, we re-align deposit qty
 *   (full reactive sync requires patching Orderline; we keep imports minimal to avoid loader issues).
 */
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
            let qty = getLineQty(line) * factor;
            if (!isFinite(qty) || qty <= 0) qty = factor;

            const depLine = await super.addLineToOrder({ productId: depProd.id, qty }, order, {}, false);
            if (depLine) {
                depLine.is_deposit = true;
                depLine.linked_line_uid = line.uid;
                line.linked_deposit_uid = depLine.uid;

                // quick one-shot re-align after immediate main qty edits (avoid heavy prototype patches)
                const prevGet = line.get_quantity?.bind(line);
                line.get_quantity = function() {
                    const q = prevGet ? prevGet() : this.quantity;
                    const expected = (q || 0) * resolveDepositFactor(order.pos || order?.env?.pos || this.pos, product);
                    if (depLine && depLine.set_quantity && isFinite(expected) && expected >= 0) {
                        try { depLine.set_quantity(expected); } catch (e) { /* ignore */ }
                    }
                    return q;
                };
            }
        } catch (e) {
            console.error(BANNER, "error in addLineToOrder:", e);
        }
        return line;
    },
});