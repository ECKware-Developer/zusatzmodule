# POS Deposit Auto Lines (Odoo 18)

Auto‑adds **deposit** lines in **POS** when a product with a configured deposit is added.

**Supported fields**
- `x_deposit_product_1` – deposit product (product.product)
- `x_quantity_by_deposit_product` – quantity multiplier (e.g., 20 for a case)
- `x_unit_sale_product` – link from case to unit product
- Fallbacks: `x_deposit_factor`, `deposit_product_id`, `x_deposit_product_id`

**How it works**
- Backend resolves the above fields per variant and exposes:
  - `pda_deposit_product_id`
  - `pda_deposit_factor`
- Frontend uses only these two keys to add the deposit line.