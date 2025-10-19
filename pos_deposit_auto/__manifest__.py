{
    "name": "POS Deposit Auto Lines (v18)",
    "summary": "Auto-add deposit product lines in POS based on custom fields (Odoo 18).",
    "version": "18.0.2.0.0",
    "category": "Point of Sale",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "product"],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_deposit_auto_v18/static/src/pos_deposit.js"
        ]
    },
    "installable": true,
    "application": false
}