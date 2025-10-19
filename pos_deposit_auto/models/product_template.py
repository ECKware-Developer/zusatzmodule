# -*- coding: utf-8 -*-
from odoo import models

DEPOSIT_FIELDS = [
    "x_deposit_product_1",
    "x_quantity_by_deposit_product",
    "x_unit_sale_product",
    "x_deposit_factor",
    "deposit_product_id",
    "x_deposit_product_id",
]

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _loader_params_product_template(self):
        """Extend the POS loader fields for product.template (defensive)."""
        params = super()._loader_params_product_template()
        fields = params.get("search_params", {}).get("fields", [])
        for fname in DEPOSIT_FIELDS:
            if fname in self._fields and fname not in fields:
                fields.append(fname)
        params["search_params"]["fields"] = fields
        return params

    def _get_pos_ui_product_template(self, params):
        return super()._get_pos_ui_product_template(params)