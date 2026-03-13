{
    'name': 'Beer hL Sales Report',
    'version': '17.0.1.0.0',
    'summary': 'Pivot report for beer sales in hectoliters from invoices and POS',
    'category': 'Sales/Reporting',
    'author': 'OpenAI',
    'license': 'LGPL-3',
    'depends': ['account', 'point_of_sale'],
    'data': [
        'views/beer_hl_sales_report_views.xml',
    ],
    'installable': True,
    'application': True,
}
