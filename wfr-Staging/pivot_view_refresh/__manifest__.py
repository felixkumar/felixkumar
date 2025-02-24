{
    'name': 'Pivot View Refresh',
    'version': '16.0.0.1',
    'summary': 'Adds a refresh button to pivot view to refresh the data',
    'description': 'Adds a refresh button to pivot view to refresh the data',
    # 'category': 'Category',
    'author': 'SIGB',
    # 'website': 'Website',
    'license': 'AGPL-3',
    'depends': ['base', 'web'],
    # 'data': ['Data'],
    # 'demo': ['Demo'],
    'installable': True,
    'auto_install': False,

    'assets': {
        'web.assets_backend': [
            '/pivot_view_refresh/static/src/js/pivot_controller_inherit.js',
            '/pivot_view_refresh/static/src/xml/pivot_view_render_inherit.xml',
        ]
    },
}
