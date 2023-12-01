# -*- coding: utf-8 -*-
{
    'name': "partner_asset",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Partner/Asset',
    'version': '15.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','contacts', 'base_geolocalize', 'stock','sale_management',],

    # always loaded
    'data': [
        'security/partner_asset_security.xml',
        'security/ir.model.access.csv',
        'views/partner_payment.xml',
        'views/res_company_view.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/partner_asset_views.xml',
        'views/partner_asset_menu.xml',
        'views/product_views.xml',
        'views/stock_picking.xml',
        'views/account_views.xml',

        'data/partner_asset_assignment_data.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'wizard/views_sale_asset_view.xml',
        'wizard/views_payment_wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'js': [
        'partner_asset/static/src/js/map_init_script.js',
    ],
    'license': 'LGPL-3',
    'installable': True,
}
