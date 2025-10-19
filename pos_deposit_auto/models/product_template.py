# -*- coding: utf-8 -*-
from odoo import models

DEPOSIT_FIELDS = [
    "x_deposit_product_1", "deposit_product_id", "x_deposit_product_id",
    "x_quantity_by_deposit_product", "x_deposit_factor",
    "x_unit_sale_product",
]

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _loader_params_product_template(self):
        params = super()._loader_params_product_template()
        fields = set(params.get("search_params", {}).get("fields", []))
        for f in DEPOSIT_FIELDS:
            if f in self._fields:
                fields.add(f)
        params["search_params"]["fields"] = list(fields)
        return params