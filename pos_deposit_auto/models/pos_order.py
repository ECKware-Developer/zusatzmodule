# -*- coding: utf-8 -*-
from odoo import api, models

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model_create_multi
    def create(self, vals_list):
        # create orders first
        orders = super().create(vals_list)
        if self.env.context.get("pda_no_deposit"):
            return orders

        for order in orders:
            # for safety, avoid double injection
            if order.lines and order.lines.filtered(lambda l: l.is_deposit):
                # already has deposit lines → skip
                continue

            for line in order.lines.sorted(key=lambda l: l.id):
                if line.is_deposit:
                    continue
                product = line.product_id
                dep, fac = product._pda_resolve_deposit()
                if not dep:
                    continue

                # If deposit line already exists and is linked, skip creating a duplicate
                existing = order.lines.filtered(lambda l: l.is_deposit and l.linked_main_line_id == line)
                if existing:
                    continue

                qty = (line.qty or 1.0) * (fac or 1.0)

                # Create deposit line; use same taxes from deposit product
                self.env["pos.order.line"].with_context(pda_no_deposit=True).create({
                    "order_id": order.id,
                    "product_id": dep.id if hasattr(dep, "id") else dep,
                    "qty": qty,
                    "price_unit": dep.lst_price if hasattr(dep, "lst_price") else dep.list_price if hasattr(dep, "list_price") else 0.0,
                    "discount": 0.0,
                    "tax_ids": [(6, 0, dep.taxes_id.ids if hasattr(dep, "taxes_id") else [])],
                    "is_deposit": True,
                    "linked_main_line_id": line.id,
                })
        return orders