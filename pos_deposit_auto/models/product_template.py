from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Make sure POS loads the deposit-related fields from product templates.
        Some databases store the deposit link on the template, others on product.product
        via delegated inheritance. We include the candidates here so the POS has them.
        """
        fields = super()._load_pos_data_fields(config_id)
        extra = []
        for fname in ("deposit_product_id", "x_deposit_factor", "x_deposit_product_id"):
            if fname in self._fields:
                extra.append(fname)
        return list(set(fields + extra))