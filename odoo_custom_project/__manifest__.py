# -*- coding: utf-8 -*-
{
    'name': "vkp_project_ext",

    'summary': """VKP project ext""",

    'description': """
        Long description of module's purpose
    """,

    'author': "CRMiUM",
    'website': "https://crmium.com/",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'project',
                'account',
                ],

    # always loaded
    'data': [
        # 'data/sequence.xml',
        'data/project_stages.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/practise.xml',
        'views/templates.xml',
        'views/email_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
