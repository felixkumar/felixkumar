# -*- coding: utf-8 -*-

{
    'name': 'Warehouse Management: Batch Transfer Extended',
    'version': '2.4',
    'category': 'Inventory/Inventory',
    'description': """
This module adds the batch transfer option in warehouse management for extended feature
==================================================================
    """,
    'depends': ['stock', 'stock_picking_batch'],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/stock_picking_batch_group_views.xml',
        'views/stock_picking_batch_views.xml',
        'views/stock_warehouse_views.xml',
        'wizard/stock_picking_to_batch_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'license': 'LGPL-3',
}
