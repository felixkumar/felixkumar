{
    'name': 'Product Identical SKU',
    'version': '16.0.0.2',
    'summary': 'Creates a model where Identical (Alternative) SKUs for products can be entered and mapped to a product',
    'description': 'Creates a model where Identical (Alternative) SKUs for products can be entered by users and '
                   'mapped to a product',
    'category': 'Inventory',
    'author': 'SIGB',
    'license': 'AGPL-3',
    'depends': ['stock', 'product', 'warefor_3pl_tus'],
    'data': [
        'data/sku_group.xml',
        'data/ir_cron.xml',
        'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/identical_sku.xml'
             ],
    'installable': True,
    'auto_install': False
}

