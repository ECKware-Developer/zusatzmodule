/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

const BANNER = "[pos_deposit_auto v18.0.7 alias]";
const PATCH_GUARD = "__pda_patch_applied__";

console.info(BANNER, "loaded");

function qtyOf(line) {
    return typeof line.get_quantity === "function" ? line.get_quantity() : line.quantity;
}

async function addDepositFor(store, order, mainLine, product) {
    try {
        const depId = product.pda_deposit_product_id;
        const factor = Number(product.pda_deposit_factor || 1);
        if (!depId || depId === product.id) return;

        const baseQty = qtyOf(mainLine) || 1;
        const qty = baseQty * (isFinite(factor) && factor > 0 ? factor : 1);

        console.warn(BANNER, "addDepositFor:", product.display_name || product.name, "depId=", depId, "factor=", factor, "qty=", qty);
        const depLine = await store.addLineToOrder({ productId: depId, qty }, order, {}, false);
        if (depLine) {
            depLine.is_deposit = true;
            depLine.linked_line_uid = mainLine.uid;
            mainLine.linked_deposit_uid = depLine.uid;
        }
    } catch (e) {
        console.error(BANNER, "addDepositFor error", e);
    }
}

function applyPatches(PosStore) {
    if (PosStore.prototype[PATCH_GUARD]) return;
    PosStore.prototype[PATCH_GUARD] = true;

    // Patch 1: addLineToOrder
    const _addLineToOrder = PosStore.prototype.addLineToOrder;
    PosStore.prototype.addLineToOrder = async function(vals, order = this.get_order(), opts = {}, configure = true) {
        const line = await _addLineToOrder.call(this, vals, order, opts, configure);
        try {
            if (!line || !order) return line;
            const product = line.product || (typeof line.get_product === "function" ? line.get_product() : null);
            if (!product || line.is_deposit) return line;
            await addDepositFor(this, order, line, product);
        } catch (e) {
            console.error(BANNER, "error in addLineToOrder", e);
        }
        return line;
    };

    // Patch 2: addProductToCurrentOrder
    if (PosStore.prototype.addProductToCurrentOrder) {
        const _addProductToCurrentOrder = PosStore.prototype.addProductToCurrentOrder;
        PosStore.prototype.addProductToCurrentOrder = async function(product, options) {
            const line = await _addProductToCurrentOrder.call(this, product, options);
            try {
                const order = this.get_order && this.get_order();
                const mainLine = line || (order && order.get_selected_orderline && order.get_selected_orderline());
                if (order && mainLine && product && !mainLine.is_deposit) {
                    await addDepositFor(this, order, mainLine, product);
                }
            } catch (e) {
                console.error(BANNER, "error in addProductToCurrentOrder", e);
            }
            return line;
        };
    }

    // Patch 3: addProduct
    if (PosStore.prototype.addProduct) {
        const _addProduct = PosStore.prototype.addProduct;
        PosStore.prototype.addProduct = async function(product, options) {
            const line = await _addProduct.call(this, product, options);
            try {
                const order = this.get_order && this.get_order();
                const mainLine = line || (order && order.get_selected_orderline && order.get_selected_orderline());
                if (order && mainLine && product && !mainLine.is_deposit) {
                    await addDepositFor(this, order, mainLine, product);
                }
            } catch (e) {
                console.error(BANNER, "error in addProduct", e);
            }
            return line;
        };
    }
}

applyPatches(PosStore);