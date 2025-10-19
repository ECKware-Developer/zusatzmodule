# -*- coding: utf-8 -*-
from odoo import models

DEPOSIT_FIELDS = [
    "x_deposit_product_1",            # user's deposit product (m2o to product.product)
    "x_quantity_by_deposit_product",  # user's factor
    "x_unit_sale_product",            # user's link to unit product
    # fallbacks
    "x_deposit_factor",
    "deposit_product_id",
    "x_deposit_product_id",
]

class ProductProduct(models.Model):
    _inherit = "product.product"

    def _loader_params_product_product(self):
        """Extend the POS loader fields for product.product (Odoo 16+/18)."""
        params = super()._loader_params_product_product()
        fields = params.get("search_params", {}).get("fields", [])
        for fname in DEPOSIT_FIELDS:
            if fname in self._fields and fname not in fields:
                fields.append(fname)
        params["search_params"]["fields"] = fields
        return params

    def _get_pos_ui_product_product(self, params):
        """No post-processing needed; keep hook for compatibility."""
        return super()._get_pos_ui_product_product(params)