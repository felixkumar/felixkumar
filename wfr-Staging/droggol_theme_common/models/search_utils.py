# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present Droggol Infotech Private Limited. (<https://www.droggol.com/>)

import re


class DroggolSearchTerm:

    _name = 'product.public.category'

    def __init__(self, ds_name, category_id, formulate, *args, **kwargs):
        self.ds_name = ds_name
        self.id = category_id
        self.formulate = formulate
        args = args
        kwargs = kwargs

    def __repr__(self):
        return f'{self.ds_name}({self.id}:{self.formulate})'


class CategorySearchDB:
    def __init__(self, db):
        self.db = db

    def search(self, term=None, categories_ids=False, options=None):
        result = []

        for category in self.db:
            if category.formulate:
                continue

            if categories_ids and category.id in categories_ids:
                result.append(category)

            if term and re.search(re.escape(term), category.ds_name, re.IGNORECASE):
                result.append(category)
        return result
