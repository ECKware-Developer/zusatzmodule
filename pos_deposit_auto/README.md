# POS Deposit Auto Lines (Odoo 18)

Auto-adds **deposit** lines in **POS** for products configured with a deposit product.

## Supported custom fields
- `x_deposit_product_1` — m2o to deposit product (product.product)
- `x_quantity_by_deposit_product` — number of deposits per main product (e.g., 20 for a case)
- `x_unit_sale_product` — case → unit link; if the case has no direct deposit, the module reads it from the linked unit product

Fallbacks also supported: `x_deposit_factor`, `deposit_product_id`, `x_deposit_product_id`.

## How it works
- Extends **POS loader** to include fields on both `product.product` and `product.template`.
- When adding a product line in POS, adds a **deposit** line (qty × factor).
- Keeps quantities **in sync** (with recursion guard).
- Removes the deposit line if the main line is removed.

## Configure
1. Create deposit products (Service, Available in POS, 0% VAT, price e.g. 0.08 €).
2. On sellable products set `x_deposit_product_1`.  
   Or leave it empty and set `x_unit_sale_product` to a unit/bottle that has `x_deposit_product_1`.
3. For cases set `x_quantity_by_deposit_product` = 20 (or your count).
4. Restart the POS session.

License: LGPL-3