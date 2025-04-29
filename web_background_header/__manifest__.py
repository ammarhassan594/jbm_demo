# -*- coding: utf-8 -*-
{
    "name": "Web Extended",
    "version": "15.0.0.1",
    "category": "Tools",
    "summary": "Header Color Change,Background Image Change.",
    "description": """
      Header Color Change,Background Image Change.
    """,
    "depends": ["web", 'web_widget_colorpicker', 'base'],
    "data": [
        "views/res_company_view.xml",
        "views/webclient_bootstrap.xml",
    ],
    'assets': {
        'web.assets_backend': [
            # 'web_background_header/static/src/js/home.js',

        ],
    },
    "demo": [],
    "qweb": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
