from odoo import models, api

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Ensure the POS receives the deposit fields on product.product as well.
        Since product.product delegates to product.template, the fields are usually
        available here too. Including them here makes the module robust across setups.
        """
        fields = super()._load_pos_data_fields(config_id)
        extra = []
        for fname in ("deposit_product_id", "x_deposit_factor", "x_deposit_product_id"):
            if fname in self._fields:
                extra.append(fname)
        return list(set(fields + extra))