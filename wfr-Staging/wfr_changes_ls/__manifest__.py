{
    'name': 'WFR Changes',
    'version': '16.0.0.23',
    'summary': 'Changes for Warefor',
    'description': 'Changes for Warefor',
    'author': 'SIGB',
    'license': 'AGPL-3',
    'depends': ['project', 'mc_freight_app', 'warefor_3pl_tus', 'user_warehouse_restriction', 'stock', 'account',
                'web_m2x_options', 'product'],
    'data': [
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/ibl_freight_inherit.xml',
        'views/project_task.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'views/storage_type_ibl.xml',
        'views/freight_order_line.xml',
        'views/freight_ibl_ops.xml',
        'views/res_users.xml',
        'views/stock_picking_batch.xml',
        'views/stock_picking_batch_group.xml',
        'views/truck_driver_name.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wfr_changes_ls/static/src/js/forecasted_buttons.js',
            'wfr_changes_ls/static/src/xml/stock_forecasted.xml'
        ]
    },
    'installable': True,
    'auto_install': False
}
