# -*- coding: utf-8 -*-
{
    'name': "PRO FORMA INVOICE",
    'author':
        'ENZAPPS',
    'summary': """
This module is for PRO FORMA INVOICE.
""",

    'description': """
This module is for PRO FORMA INVOICE.
    """,
    'website': "",
    'category': 'base',
    'version': '14.0',
    'depends': ['base', 'account', 'stock','mail'],
    "images": ['static/description/icon.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/pro_forma_invoice.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
}
