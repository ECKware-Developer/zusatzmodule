# -*- coding: utf-8 -*-
from odoo import models

# Fields we want in the POS cache
DEPOSIT_FIELDS = [
    "x_deposit_product_1",            # user's deposit product (m2o to product.product)
    "x_quantity_by_deposit_product",  # user's factor
    "x_unit_sale_product",            # case -> unit product link
    # fallbacks seen elsewhere
    "x_deposit_factor",
    "deposit_product_id",
    "x_deposit_product_id",
]

class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_product_product(self):
        """Extend the POS loader fields for product.product (Odoo 16+/18)."""
        params = super()._loader_params_product_product()
        fields = params.get("search_params", {}).get("fields", [])
        for fname in DEPOSIT_FIELDS:
            if fname in self.env['product.product']._fields and fname not in fields:
                fields.append(fname)
        params["search_params"]["fields"] = fields
        return params

    def _loader_params_product_template(self):
        """Extend the POS loader fields for product.template for completeness."""
        params = super()._loader_params_product_template()
        fields = params.get("search_params", {}).get("fields", [])
        for fname in DEPOSIT_FIELDS:
            if fname in self.env['product.template']._fields and fname not in fields:
                fields.append(fname)
        params["search_params"]["fields"] = fields
        return params