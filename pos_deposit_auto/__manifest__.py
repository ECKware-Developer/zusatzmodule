# -*- coding: utf-8 -*-
{
    "name": "POS Deposit Auto Lines (v18)",
    "summary": "Auto-add deposit lines in POS using custom fields; robust mapping (Odoo 18).",
    "version": "18.0.5.0.0",
    "category": "Point of Sale",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "product"],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_deposit_auto/static/src/pos_deposit.js",
        ]
    },
    "installable": True,
    "application": False
}