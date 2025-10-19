# -*- coding: utf-8 -*-
from odoo import models

# Field names present in the user's DB (and fallbacks we've seen elsewhere)
FIELDS = {
    "deposit_product": ["x_deposit_product_1", "deposit_product_id", "x_deposit_product_id"],
    "qty_factor": ["x_quantity_by_deposit_product", "x_deposit_factor"],
    "unit_link": ["x_unit_sale_product"],
}

class PosSession(models.Model):
    _inherit = "pos.session"

    # --- Loader params: ensure we fetch base fields we need ---
    def _loader_params_product_product(self):
        params = super()._loader_params_product_product()
        fields = set(params.get("search_params", {}).get("fields", []))
        # we always need product_tmpl_id to read template-level values
        fields.add("product_tmpl_id")
        for name in FIELDS["deposit_product"] + FIELDS["qty_factor"] + FIELDS["unit_link"]:
            if name in self.env["product.product"]._fields:
                fields.add(name)
        params["search_params"]["fields"] = list(fields)
        return params

    def _loader_params_product_template(self):
        params = super()._loader_params_product_template()
        fields = set(params.get("search_params", {}).get("fields", []))
        for name in FIELDS["deposit_product"] + FIELDS["qty_factor"] + FIELDS["unit_link"]:
            if name in self.env["product.template"]._fields:
                fields.add(name)
        params["search_params"]["fields"] = list(fields)
        return params

    # --- Post-process: inject resolved deposit info directly on product dict ---
    def _get_pos_ui_product_product(self, params):
        records = super()._get_pos_ui_product_product(params)
        # Build map of template values to avoid N+1
        tmpl_ids = [rec.get("product_tmpl_id") and (rec["product_tmpl_id"][0] if isinstance(rec["product_tmpl_id"], (list, tuple)) else rec["product_tmpl_id"]) for rec in records]
        tmpl_ids = [i for i in tmpl_ids if i]
        tmpl_by_id = {}
        if tmpl_ids:
            templates = self.env["product.template"].sudo().browse(tmpl_ids)
            for t in templates:
                tmpl_by_id[t.id] = {
                    "deposit_product": next((getattr(t, f).id for f in FIELDS["deposit_product"] if f in t and getattr(t, f)), None),
                    "qty_factor": next((getattr(t, f) for f in FIELDS["qty_factor"] if f in t and getattr(t, f)), None),
                    "unit_link": next((getattr(t, f).id for f in FIELDS["unit_link"] if f in t and getattr(t, f)), None),
                }

        # Helper to get first truthy attr from a product dict (variant)
        def _get_variant_value(rec, names):
            for f in names:
                if f in rec and rec[f]:
                    v = rec[f]
                    if isinstance(v, (list, tuple)):
                        return v[0]
                    if isinstance(v, dict) and "id" in v:
                        return v["id"]
                    return v
            return None

        for rec in records:
            # Resolve from variant
            dep_id = _get_variant_value(rec, FIELDS["deposit_product"])
            qty_factor = _get_variant_value(rec, FIELDS["qty_factor"])
            unit_id = _get_variant_value(rec, FIELDS["unit_link"])

            # If missing, fallback to template
            tmpl_id = rec.get("product_tmpl_id")
            tmpl_id = tmpl_id[0] if isinstance(tmpl_id, (list, tuple)) else tmpl_id
            tmpl_vals = tmpl_by_id.get(tmpl_id, {}) if tmpl_id else {}

            if not dep_id:
                dep_id = tmpl_vals.get("deposit_product")

            if unit_id and not dep_id:
                # Resolve deposit via unit product (variant) if possible
                unit_prod = self.env["product.product"].sudo().browse(unit_id)
                if unit_prod.exists():
                    # Try variant fields on unit first
                    for f in FIELDS["deposit_product"]:
                        val = getattr(unit_prod, f, False)
                        if val:
                            dep_id = val.id if hasattr(val, "id") else val
                            break
                    # Fallback to unit's template
                    if not dep_id and unit_prod.product_tmpl_id:
                        for f in FIELDS["deposit_product"]:
                            val = getattr(unit_prod.product_tmpl_id, f, False)
                            if val:
                                dep_id = val.id if hasattr(val, "id") else val
                                break

            # Factor fallback chain
            if qty_factor in (None, False, 0):
                qty_factor = tmpl_vals.get("qty_factor")
            if (qty_factor in (None, False, 0)) and unit_id:
                unit_prod = self.env["product.product"].sudo().browse(unit_id)
                if unit_prod.exists():
                    for f in FIELDS["qty_factor"]:
                        val = getattr(unit_prod, f, False)
                        if val:
                            qty_factor = val
                            break
                    if (qty_factor in (None, False, 0)) and unit_prod.product_tmpl_id:
                        for f in FIELDS["qty_factor"]:
                            val = getattr(unit_prod.product_tmpl_id, f, False)
                            if val:
                                qty_factor = val
                                break

            # Defaults
            if not qty_factor:
                qty_factor = 1

            # Inject resolved keys for the POS JS (simple integers)
            rec["pda_deposit_product_id"] = dep_id or False
            rec["pda_deposit_factor"] = qty_factor

        return records