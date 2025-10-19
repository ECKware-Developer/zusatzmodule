# -*- coding: utf-8 -*-
from odoo import models

FIELDS = {
    "deposit_product": ["x_deposit_product_1", "deposit_product_id", "x_deposit_product_id"],
    "qty_factor": ["x_quantity_by_deposit_product", "x_deposit_factor"],
    "unit_link": ["x_unit_sale_product"],
}

class ProductProduct(models.Model):
    _inherit = "product.product"

    def _pda_first_val(self, rec, names):
        for f in names:
            if hasattr(rec, f):
                val = getattr(rec, f)
                if val:
                    return val
        return False

    def _pda_resolve_deposit(self):
        """Return (deposit_product, quantity_factor) for self (single) using variant, template, and unit link fallbacks."""
        self.ensure_one()
        # Try variant direct
        dep = self._pda_first_val(self, FIELDS["deposit_product"])
        fac = self._pda_first_val(self, FIELDS["qty_factor"])

        # Template fallbacks
        if self.product_tmpl_id:
            if not dep:
                dep = self._pda_first_val(self.product_tmpl_id, FIELDS["deposit_product"])
            if not fac:
                fac = self._pda_first_val(self.product_tmpl_id, FIELDS["qty_factor"])

        # Unit link (e.g., case -> unit)
        unit = self._pda_first_val(self, FIELDS["unit_link"]) or (self.product_tmpl_id and self._pda_first_val(self.product_tmpl_id, FIELDS["unit_link"]))
        if unit and not dep:
            dep = self._pda_first_val(unit, FIELDS["deposit_product"]) or (unit.product_tmpl_id and self._pda_first_val(unit.product_tmpl_id, FIELDS["deposit_product"]))
        if unit and not fac:
            fac = self._pda_first_val(unit, FIELDS["qty_factor"]) or (unit.product_tmpl_id and self._pda_first_val(unit.product_tmpl_id, FIELDS["qty_factor"]))

        # Defaults
        fac = fac or 1
        return (dep if getattr(dep, "id", False) or dep else False, fac)