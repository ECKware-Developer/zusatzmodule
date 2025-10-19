{
    "name": "POS Deposit Auto Lines (v18)",
    "summary": "Automatically add bottle/case deposit product lines in POS (Odoo 18).",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "author": "Custom",
    "website": "https://example.com",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "product"],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_deposit_auto/static/src/pos_deposit.js"
        ]
    },
    "installable": true,
    "application": false
}