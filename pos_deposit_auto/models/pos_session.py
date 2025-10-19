# -*- coding: utf-8 -*-
from odoo import models

FIELDS = {
    "deposit_product": ["x_deposit_product_1", "deposit_product_id", "x_deposit_product_id"],
    "qty_factor": ["x_quantity_by_deposit_product", "x_deposit_factor"],
    "unit_link": ["x_unit_sale_product"],
}

class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_product_product(self):
        params = super()._loader_params_product_product()
        fields = set(params.get("search_params", {}).get("fields", []))
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

    def _get_pos_ui_product_product(self, params):
        records = super()._get_pos_ui_product_product(params)
        # Preload templates for fewer lookups
        tmpl_ids = []
        for rec in records:
            pt = rec.get("product_tmpl_id")
            if isinstance(pt, (list, tuple)):
                pt = pt[0]
            if pt:
                tmpl_ids.append(pt)
        tmpl_ids = list(set(tmpl_ids))
        tmpl_map = {}
        if tmpl_ids:
            for t in self.env["product.template"].sudo().browse(tmpl_ids):
                tmpl_map[t.id] = {
                    "dep": next((getattr(t, f).id for f in FIELDS["deposit_product"] if hasattr(t, f) and getattr(t, f)), None),
                    "fac": next((getattr(t, f) for f in FIELDS["qty_factor"] if hasattr(t, f) and getattr(t, f)), None),
                    "unit": next((getattr(t, f).id for f in FIELDS["unit_link"] if hasattr(t, f) and getattr(t, f)), None),
                }

        def _from_variant(rec, names):
            for f in names:
                v = rec.get(f)
                if v:
                    if isinstance(v, (list, tuple)):
                        return v[0]
                    if isinstance(v, dict) and "id" in v:
                        return v["id"]
                    return v
            return None

        for rec in records:
            dep_id = _from_variant(rec, FIELDS["deposit_product"])
            fac = _from_variant(rec, FIELDS["qty_factor"])
            unit_id = _from_variant(rec, FIELDS["unit_link"])

            pt = rec.get("product_tmpl_id")
            if isinstance(pt, (list, tuple)): pt = pt[0]
            tvals = tmpl_map.get(pt, {})

            if not dep_id:
                dep_id = tvals.get("dep")

            if unit_id and not dep_id:
                unit = self.env["product.product"].sudo().browse(unit_id)
                if unit.exists():
                    for f in FIELDS["deposit_product"]:
                        val = getattr(unit, f, False)
                        if val:
                            dep_id = val.id if hasattr(val, "id") else val
                            break
                    if not dep_id and unit.product_tmpl_id:
                        for f in FIELDS["deposit_product"]:
                            val = getattr(unit.product_tmpl_id, f, False)
                            if val:
                                dep_id = val.id if hasattr(val, "id") else val
                                break

            if not fac:
                fac = tvals.get("fac")
            if (not fac or fac == 0) and unit_id:
                unit = self.env["product.product"].sudo().browse(unit_id)
                if unit.exists():
                    for f in FIELDS["qty_factor"]:
                        val = getattr(unit, f, False)
                        if val:
                            fac = val
                            break
                    if (not fac or fac == 0) and unit.product_tmpl_id:
                        for f in FIELDS["qty_factor"]:
                            val = getattr(unit.product_tmpl_id, f, False)
                            if val:
                                fac = val
                                break

            rec["pda_deposit_product_id"] = dep_id or False
            rec["pda_deposit_factor"] = fac or 1
        return records