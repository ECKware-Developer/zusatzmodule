# POS Deposit Auto Lines (Odoo 18)

Automatically adds bottle/case **deposit** product lines in **POS** when a product with a linked **deposit product** is added.
Designed for **Odoo 18** where OCA alternatives are not yet ported.

## How it works
- Add a Many2one field on the sellable product that points to the **deposit product**.
  - In Odoo Industries *Beverages*, this field usually exists as **`deposit_product_id`** (shown as *Pfandprodukt*).
  - If you use a Studio field instead, name it e.g. **`x_deposit_product_id`**; the module will pick it up too.
- Optionally add a numeric field **`x_deposit_factor`** on the main product (default = 1). Use it to multiply deposits (e.g. a case with 20 bottles).

The module:
- loads the necessary fields into the POS cache;
- when a main product line is added, **auto-adds** a second line for the deposit product (same qty × factor);
- keeps both quantities **in sync**;
- removes the deposit line if the main line is removed.

## Configuration checklist
1. Create deposit products (type **Service**, **Available in POS**, **0% VAT**, price e.g. 0.08 €).
2. On each beverage product, set **Pfandprodukt** (`deposit_product_id`) to the right deposit product.
3. (Optional) Add **`x_deposit_factor`** = 20 for cases, 1 for single bottles.
4. Restart the POS session.

## Notes
- Deposit appears as its own POS line (legally cleaner, TSE-friendly).
- The module is small and does not change accounting logic; use your own accounts for the deposit product/category.
- If your database uses a custom field for the deposit link, add its technical name to the arrays in:
  - `models/product_template.py` and `models/product_product.py`
  - `static/src/pos_deposit.js` (function `getDepositProductId`).

License: LGPL-3