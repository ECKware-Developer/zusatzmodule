# -*- coding: utf-8 -*-
{
    "name": "POS Deposit Auto Lines (v18, server-side)",
    "summary": "Adds deposit lines on the server when POS orders are created (Odoo 18).",
    "version": "18.0.10.0.0",
    "category": "Point of Sale",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "product"],
    "data": [
        "security/ir.model.access.csv"
    ],
    "installable": True,
    "application": False
}