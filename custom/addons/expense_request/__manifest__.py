# -*- coding: utf-8 -*-
{
    'name': "expense_request",

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
    'category': 'Human Resources/Depenses',
    'version': '15.0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_contract', 'account', "analytic_multi_dimension",],

    # always loaded
    'data': [
        'security/expense_request_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/res_config_settings_views.xml',
        'views/expense_request_views.xml',
        'views/expense_request_menu.xml',
        #data
        'data/expense_request_seq.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
}
