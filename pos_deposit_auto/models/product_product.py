# -*- coding: utf-8 -*-
from odoo import models

FIELDS = {
    "deposit_product": ["x_deposit_product_1", "deposit_product_id", "x_deposit_product_id"],
    "qty_factor": ["x_quantity_by_deposit_product", "x_deposit_factor"],
    "unit_link": ["x_unit_sale_product"],
}

class ProductProduct(models.Model):
    _inherit = "product.product"

    def _loader_params_product_product(self):
        params = super()._loader_params_product_product()
        fields = set(params.get("search_params", {}).get("fields", []))
        fields.add("product_tmpl_id")
        for name in FIELDS["deposit_product"] + FIELDS["qty_factor"] + FIELDS["unit_link"]:
            if name in self._fields:
                fields.add(name)
        params["search_params"]["fields"] = list(fields)
        return params

    def _get_pos_ui_product_product(self, params):
        res = super()._get_pos_ui_product_product(params)
        tmpl_ids = set()
        unit_ids = set()
        for rec in res:
            pt = rec.get("product_tmpl_id")
            if isinstance(pt, (list, tuple)):
                pt = pt[0]
            if pt:
                tmpl_ids.add(pt)
            for f in FIELDS["unit_link"]:
                v = rec.get(f)
                if isinstance(v, (list, tuple)):
                    v = v[0]
                if v:
                    unit_ids.add(v)
        tmpl_map = {}
        if tmpl_ids:
            for t in self.env["product.template"].sudo().browse(list(tmpl_ids)):
                dep = next((getattr(t, f).id for f in FIELDS["deposit_product"] if hasattr(t, f) and getattr(t, f)), None)
                fac = next((getattr(t, f) for f in FIELDS["qty_factor"] if hasattr(t, f) and getattr(t, f)), None)
                unit = next((getattr(t, f).id for f in FIELDS["unit_link"] if hasattr(t, f) and getattr(t, f)), None)
                tmpl_map[t.id] = {"dep": dep, "fac": fac, "unit": unit}
        unit_map = {}
        if unit_ids:
            for p in self.env["product.product"].sudo().browse(list(unit_ids)):
                unit_map[p.id] = {
                    "dep": next((getattr(p, f).id for f in FIELDS["deposit_product"] if hasattr(p, f) and getattr(p, f)), None),
                    "fac": next((getattr(p, f) for f in FIELDS["qty_factor"] if hasattr(p, f) and getattr(p, f)), None),
                    "tmpl": p.product_tmpl_id.id if p.product_tmpl_id else None,
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
        for rec in res:
            dep_id = _from_variant(rec, FIELDS["deposit_product"])
            fac = _from_variant(rec, FIELDS["qty_factor"])
            unit_id = _from_variant(rec, FIELDS["unit_link"])
            pt = rec.get("product_tmpl_id")
            if isinstance(pt, (list, tuple)):
                pt = pt[0]
            tvals = tmpl_map.get(pt, {})
            if not dep_id:
                dep_id = tvals.get("dep")
            if unit_id and not dep_id:
                um = unit_map.get(unit_id, {})
                dep_id = um.get("dep") or (tmpl_map.get(um.get("tmpl") or 0, {}).get("dep") if um.get("tmpl") else None)
            if not fac:
                fac = tvals.get("fac")
            if (not fac or fac == 0) and unit_id:
                um = unit_map.get(unit_id, {})
                fac = um.get("fac") or (tmpl_map.get(um.get("tmpl") or 0, {}).get("fac") if um.get("tmpl") else None) or fac
            rec["pda_deposit_product_id"] = dep_id or False
            rec["pda_deposit_factor"] = fac or 1
        return res