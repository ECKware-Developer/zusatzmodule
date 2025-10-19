POS Deposit Auto Lines (Odoo 18)
================================

This addon auto-adds **deposit** lines in the **POS** when a product
configured with a deposit product is added to the order.

Supported custom fields
-----------------------

* ``x_deposit_product_1`` — m2o to deposit product (``product.product``).
* ``x_quantity_by_deposit_product`` — number of deposits per main unit.
* ``x_unit_sale_product`` — case → unit link; if the case has no
  direct deposit set, the unit product's deposit will be used.

Configuration
-------------

1. Create deposit products (Service, Available in POS, 0% VAT).
2. On each sellable product set ``x_deposit_product_1`` or
   set ``x_unit_sale_product`` and configure the deposit on that unit .
3. For cases set ``x_quantity_by_deposit_product`` to the number of units.

Restart the POS session after installing/updating the module.

License: LGPL-3