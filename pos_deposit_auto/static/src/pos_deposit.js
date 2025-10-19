/** @odoo-module **/
/*
 * POS Deposit Auto Lines (Odoo 18)
 * - Reads custom fields on products:
 *    - x_deposit_product_1: Many2one to product.product (the deposit product)
 *    - x_quantity_by_deposit_product: Float/Integer factor (e.g., 20 for a case)
 *    - x_unit_sale_product: Many2one to product.product (unit product); if the
 *      main product has no x_deposit_product_1, we try to inherit deposit
 *      from this unit product.
 * - When a product is added, auto-adds a deposit line (qty * factor).
 * - Keeps quantities in sync; removing main line removes its deposit.
 */

import { patch } from "@web/core/utils/patch";
import { Order, Orderline } from "@point_of_sale/app/store/models";

function m2oToId(value) {
    if (!value) return null;
    if (typeof value === "number") return value;
    if (Array.isArray(value)) return value[0];
    if (typeof value === "object" && value.id) return value.id;
    return null;
}

function getDepositFactor(prod) {
    const v = prod?.x_quantity_by_deposit_product;
    const n = (v === 0 || v) ? Number(v) : 1;
    return isFinite(n) && n > 0 ? n : 1;
}

function getQty(line) {
    if (typeof line.get_quantity === "function") return line.get_quantity();
    return line.quantity ?? 0;
}

function getPos(envOrObj) {
    return envOrObj?.pos || envOrObj?.env?.pos || window?.posmodel || null;
}

function getProductById(pos, id) {
    if (!pos || !id) return null;
    // Odoo 18 still ships PosDB; prefer it
    if (pos.db && typeof pos.db.get_product_by_id === "function") {
        return pos.db.get_product_by_id(id);
    }
    // Fallback: some builds expose products on pos.models
    if (pos.models) {
        const products = pos.models["product.product"] || pos.models.product || {};
        if (products[id]) return products[id];
        if (Array.isArray(products)) {
            const found = products.find((p) => p.id === id);
            if (found) return found;
        }
    }
    return null;
}

function resolveDepositProductId(prod, pos) {
    // 1) Direct field on the product
    let depId = m2oToId(prod?.x_deposit_product_1);
    if (depId) return depId;
    // 2) Inherit from unit sale product if present
    const unitId = m2oToId(prod?.x_unit_sale_product);
    if (unitId) {
        const unitProd = getProductById(pos, unitId);
        if (unitProd) {
            depId = m2oToId(unitProd.x_deposit_product_1);
            if (depId) return depId;
        }
    }
    return null;
}

// --- 1) Auto-add deposit after a product is added ---
patch(Order.prototype, {
    add_product(product, options = {}) {
        // Call parent to create/merge the main line
        const mainLine = super.add_product(product, options);
        try {
            // Guard: do not recurse when we add the deposit line itself
            if (options?.is_deposit) {
                return mainLine;
            }
            const pos = getPos(this);
            if (!pos || !product) return mainLine;

            // If a deposit is already linked (due to merge), just sync its quantity and exit
            if (mainLine.linked_deposit_uid) {
                const factor = getDepositFactor(product);
                const dep = this.get_orderlines().find((l) => l.uid === mainLine.linked_deposit_uid);
                if (dep) {
                    const newQty = getQty(mainLine) * factor;
                    Orderline.prototype.set_quantity.call(dep, newQty, options?.keep_price);
                    return mainLine;
                }
            }

            const depProdId = resolveDepositProductId(product, pos);
            if (!depProdId) return mainLine;
            if (depProdId === product.id) return mainLine;  // nonsense config guard

            const depProd = getProductById(pos, depProdId);
            if (!depProd) {
                console.warn("[pos_deposit_auto] Deposit product not loaded/available in POS:", depProdId);
                return mainLine;
            }

            // compute qty * factor based on the final merged quantity of the main line
            const factor = getDepositFactor(product);
            const qty = getQty(mainLine) * factor;
            if (!qty) return mainLine;

            // Create deposit line
            const depLine = super.add_product(depProd, {
                quantity: qty,
                is_deposit: true,
                // keep default price (depProd.lst_price in POS)
            });

            if (depLine) {
                depLine.is_deposit = true;
                depLine.linked_line_uid = mainLine.uid;
                mainLine.linked_deposit_uid = depLine.uid;
            }
        } catch (e) {
            console.warn("[pos_deposit_auto] add_product error:", e);
        }
        return mainLine;
    },
});

// --- 2) Keep quantities in sync ---
patch(Orderline.prototype, {
    set_quantity(qty, keep_price) {
        const res = super.set_quantity(qty, keep_price);
        try {
            const order = this.order;
            if (!order) return res;

            // If main line changed, update deposit
            if (this.linked_deposit_uid) {
                const dep = order.get_orderlines().find((l) => l.uid === this.linked_deposit_uid);
                if (dep) {
                    const factor = getDepositFactor(this.product || {});
                    const newQty = getQty(this) * factor;
                    // Avoid recursion by calling super on deposit directly
                    Orderline.prototype.set_quantity.call(dep, newQty, keep_price);
                }
            }

            // If deposit line changed, enforce sync back to main
            if (this.is_deposit && this.linked_line_uid) {
                const main = order.get_orderlines().find((l) => l.uid === this.linked_line_uid);
                if (main) {
                    const factor = getDepositFactor(main.product || {});
                    const newQty = getQty(main) * factor;
                    super.set_quantity(newQty, keep_price);
                }
            }
        } catch (e) {
            console.warn("[pos_deposit_auto] sync qty error:", e);
        }
        return res;
    },
});

// --- 3) Remove linked deposit when main is removed; unlink if deposit removed ---
patch(Order.prototype, {
    removeOrderline(line) {
        const isDeposit = line?.is_deposit;
        const linkedUid = line?.linked_line_uid || line?.linked_deposit_uid;
        const res = super.removeOrderline(line);
        try {
            if (!linkedUid) return res;
            const other = this.get_orderlines().find((l) => l.uid === linkedUid);
            if (!other) return res;
            if (!isDeposit && other.is_deposit) {
                // removed main -> also remove deposit
                super.removeOrderline(other);
            }
            if (isDeposit && other) {
                // removed deposit -> just unlink
                delete other.linked_deposit_uid;
            }
        } catch (e) {
            console.warn("[pos_deposit_auto] remove link error:", e);
        }
        return res;
    },
});