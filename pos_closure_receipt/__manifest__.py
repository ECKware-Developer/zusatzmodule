{
    "name": "POS Closure Receipt (Tips & Cash)",
    "summary": "Druck eines Abschlussbons mit Trinkgeld- und Barbestandsübersicht im POS",
    "version": "18.0.1.1.0",
    "category": "Point of Sale",
    "author": "ECKware",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "views/pos_config_views.xml"
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_closure_receipt/static/src/js/closure_receipt.js",
            "pos_closure_receipt/static/src/xml/closure_receipt.xml"
        ]
    },
    "installable": True
}
