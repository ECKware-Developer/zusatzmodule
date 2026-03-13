# Beer hL Sales Report

This module adds a SQL-view based reporting model `x_beer_hl_sales_report` for Odoo.sh.

## What it does

It combines:
- posted customer invoices / credit notes (`account.move.line`)
- POS order lines from paid/done/invoiced orders (`pos.order.line`)

and calculates:
- sold quantity
- hL per unit from `product.template.x_studio_inhalt_in_hl`
- total sold hL (`quantity * hL per unit`)

## Result

After installation you get a new menu:
- **Accounting -> Reporting -> Beer Reporting -> Beer hL Sales**

Recommended pivot setup:
- Rows: Customer
- Columns: Date -> Month
- Measure: Sold hL

## Assumptions

- The custom Studio field exists on the product template and is named exactly `x_studio_inhalt_in_hl`.
- Only products with a non-zero hL value are included.
- Credit notes are counted negative.
- POS lines without a customer remain without `partner_id` and show up as empty customer.

## Notes

If your Odoo version uses a different Accounting/Reporting menu parent, you may need to adapt the menu parent XML id.
