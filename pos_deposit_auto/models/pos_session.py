from odoo import models

DEPOSIT_FIELDS = ["x_deposit_product_1", "x_quantity_by_deposit_product", "x_unit_sale_product"]

class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_product_product(self):
        """Ensure POS loads custom deposit-related fields on product.product.
        In Odoo 16+ the loader hooks live on pos.session as _loader_params_<model>.
        """
        res = super()._loader_params_product_product()
        fields = res.get("search_params", {}).get("fields", [])
        # robust check: only add fields that actually exist (on product.product via _inherits)
        product_model = self.env["product.product"]
        for fname in DEPOSIT_FIELDS:
            if fname in product_model._fields and fname not in fields:
                fields.append(fname)
        # write back
        res["search_params"]["fields"] = fields
        return res