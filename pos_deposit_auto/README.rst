POS Deposit Auto Lines (Odoo 18)
=================================

This addon auto-adds **deposit** lines in the **POS** when a product
configured with a deposit is added. It resolves your Studio fields on both
product variants and templates and exposes simple keys to the POS:

* ``pda_deposit_product_id`` — resolved deposit product (product.product id)
* ``pda_deposit_factor`` — resolved quantity multiplier

Supported input fields
----------------------
- ``x_deposit_product_1`` (m2o to product.product)
- ``x_quantity_by_deposit_product`` (numeric factor)
- ``x_unit_sale_product`` (link to unit product for cases)
- fallbacks: ``x_deposit_factor``, ``deposit_product_id``, ``x_deposit_product_id``

Configuration
-------------
1. Create deposit products (Service, Available in POS, 0% VAT).
2. On the beverage product set ``x_deposit_product_1``; for cases you may set
   ``x_unit_sale_product`` (pointing to the unit product with a deposit) and
   ``x_quantity_by_deposit_product`` (e.g., 20).
3. Restart the POS session.

License: LGPL-3