# -*- coding: utf-8 -*-
{
    "name": "POS Deposit Auto Lines (v18)",
    "summary": "Auto-add deposit lines in POS using custom fields; legacy-compatible patch (Odoo 18 prod bundle).",
    "version": "18.0.9.0.0",
    "category": "Point of Sale",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "product"],
    "assets": {
        "point_of_sale.assets": [
            "pos_deposit_auto/static/src/pos_deposit_legacy.js"
        ],
        "point_of_sale._assets_pos": [
            "pos_deposit_auto/static/src/pos_deposit_legacy.js"
        ]
    },
    "installable": True,
    "application": False
}