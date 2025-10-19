odoo.define('pos_deposit_auto/pos_deposit_legacy', function (require) {
    'use strict';
    var models;
    try {
        models = require('point_of_sale.models');
    } catch (e) {
        console.error('[pos_deposit_auto v18.0.9] cannot require point_of_sale.models', e);
        return;
    }
    console.info('[pos_deposit_auto v18.0.9] legacy patch active');

    var PosModel = models.PosModel;
    var Order = models.Order;
    var Orderline = models.Orderline;

    // Guard to avoid double patch
    if (Order.prototype.__pda_legacy_patched__) {
        return;
    }
    Order.prototype.__pda_legacy_patched__ = true;

    function qtyOf(line) {
        if (!line) { return 0; }
        if (line.get_quantity) { return line.get_quantity(); }
        return line.quantity || 0;
    }

    // Helper to add deposit line
    Order.prototype._pda_add_deposit_for = async function(mainLine, product) {
        try {
            if (!mainLine || !product) { return; }
            var depId = product.pda_deposit_product_id;
            var factor = Number(product.pda_deposit_factor || 1);
            if (!depId || depId === product.id) { return; }

            var depProduct = (this.pos.db && this.pos.db.get_product_by_id && this.pos.db.get_product_by_id(depId)) || (this.pos.product_by_id && this.pos.product_by_id[depId]);
            if (!depProduct) {
                console.warn('[pos_deposit_auto] deposit product not in POS cache', depId);
                return;
            }
            var baseQty = qtyOf(mainLine) || 1;
            var depQty = baseQty * (isFinite(factor) && factor > 0 ? factor : 1);

            // mark to avoid recursion
            var opts = {quantity: depQty, merge: false, extras: {is_deposit: true}};
            var depLine = this.add_product(depProduct, opts);
            if (depLine) {
                depLine.is_deposit = true;
                depLine.linked_main_cid = mainLine.cid;
                mainLine.linked_deposit_cid = depLine.cid;
            }
        } catch (e) {
            console.error('[pos_deposit_auto] _pda_add_deposit_for error', e);
        }
    };

    // Patch add_product on Order (legacy-compatible)
    var _super_add_product = Order.prototype.add_product;
    Order.prototype.add_product = function(product, options) {
        var line = _super_add_product.call(this, product, options);
        try {
            if (!product) { return line; }
            // prevent recursion if deposit line triggers again
            if (options && options.extras && options.extras.is_deposit) { return line; }
            // skip if selected line is already a deposit
            var selected = this.get_selected_orderline && this.get_selected_orderline();
            if (selected && selected.is_deposit) { return line; }
            // schedule to run after Odoo has finalized the main line (safe tick)
            var self = this;
            setTimeout(function(){
                var mainLine = self.get_selected_orderline && self.get_selected_orderline();
                if (mainLine && mainLine.product && mainLine.product.id === product.id) {
                    self._pda_add_deposit_for(mainLine, product);
                }
            }, 0);
        } catch (e) {
            console.error('[pos_deposit_auto] add_product error', e);
        }
        return line;
    };

    // Light quantity sync: when main line qty changes, re-sync deposit qty
    var _super_set_quantity = Orderline.prototype.set_quantity;
    Orderline.prototype.set_quantity = function(quantity, keep_price) {
        var res = _super_set_quantity.call(this, quantity, keep_price);
        try {
            if (this.is_deposit) { return res; }
            if (!this.order) { return res; }
            var lines = this.order.get_orderlines ? this.order.get_orderlines() : [];
            var dep = null;
            for (var i=0; i<lines.length; i++) {
                if (lines[i].is_deposit && lines[i].linked_main_cid === this.cid) {
                    dep = lines[i];
                    break;
                }
            }
            if (dep) {
                var factor = Number((this.product && this.product.pda_deposit_factor) || 1);
                var expected = (qtyOf(this) || 1) * (isFinite(factor) && factor > 0 ? factor : 1);
                if (dep.set_quantity) {
                    dep.set_quantity(expected, keep_price);
                }
            }
        } catch (e) {
            console.error('[pos_deposit_auto] set_quantity sync error', e);
        }
        return res;
    };

});