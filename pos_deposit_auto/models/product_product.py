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
        """Compute deposit mapping for POS UI: pda_deposit_product_id / pda_deposit_factor.
        Works even if fields are only on the template or split between case/unit.
        """
        res = super()._get_pos_ui_product_product(params)
        # Collect template ids and unit links to prefetch
        tmpl_ids = set()
        unit_prod_ids = set()
        for rec in res:
            pt = rec.get("product_tmpl_id")
            if isinstance(pt, (list, tuple)):
                pt = pt[0]
            if pt:
                tmpl_ids.add(pt)
            # potential unit link on variant side
            for f in FIELDS["unit_link"]:
                v = rec.get(f)
                if isinstance(v, (list, tuple)):
                    v = v[0]
                if v:
                    unit_prod_ids.add(v)
        # Prefetch templates and unit products
        tmpl_map = {}
        if tmpl_ids:
            for t in self.env["product.template"].sudo().browse(list(tmpl_ids)):
                vals = {}
                # deposit product
                dep = None
                for f in FIELDS["deposit_product"]:
                    if hasattr(t, f) and getattr(t, f):
                        val = getattr(t, f)
                        dep = val.id if hasattr(val, "id") else val
                        if dep:
                            break
                # qty factor
                fac = None
                for f in FIELDS["qty_factor"]:
                    if hasattr(t, f) and getattr(t, f):
                        fac = getattr(t, f)
                        if fac:
                            break
                # unit link
                unit = None
                for f in FIELDS["unit_link"]:
                    if hasattr(t, f) and getattr(t, f):
                        u = getattr(t, f)
                        unit = u.id if hasattr(u, "id") else u
                        if unit:
                            break
                tmpl_map[t.id] = {"dep": dep, "fac": fac, "unit": unit}

        unit_map = {}
        if unit_prod_ids:
            for p in self.env["product.product"].sudo().browse(list(unit_prod_ids)):
                unit_map[p.id] = {
                    "dep": next((getattr(p, f).id for f in FIELDS["deposit_product"]
                                 if hasattr(p, f) and getattr(p, f)), None),
                    "fac": next((getattr(p, f) for f in FIELDS["qty_factor"]
                                 if hasattr(p, f) and getattr(p, f)), None),
                    "tmpl": p.product_tmpl_id.id if p.product_tmpl_id else None,
                }

        # Helper for variant dict
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
            if isinstance(pt, (list, tuple)): pt = pt[0]
            tvals = tmpl_map.get(pt, {})

            if not dep_id:
                dep_id = tvals.get("dep")

            if unit_id and not dep_id:
                # From unit product record
                um = unit_map.get(unit_id, {})
                dep_id = um.get("dep")
                if not dep_id and um.get("tmpl"):
                    t2 = tmpl_map.get(um["tmpl"], {})
                    dep_id = t2.get("dep")

            if not fac:
                fac = tvals.get("fac")
            if (not fac or fac == 0) and unit_id:
                um = unit_map.get(unit_id, {})
                fac = um.get("fac") or fac
                if (not fac or fac == 0) and um.get("tmpl"):
                    t2 = tmpl_map.get(um["tmpl"], {})
                    fac = t2.get("fac") or fac

            if not fac:
                fac = 1

            rec["pda_deposit_product_id"] = dep_id or False
            rec["pda_deposit_factor"] = fac or 1

        return res