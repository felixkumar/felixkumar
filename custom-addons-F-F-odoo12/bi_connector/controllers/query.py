import random
from odoo import http
from odoo.http import request
from datetime import datetime, date


class QueryBuilder(http.Controller):

    @http.route('/api_bi/records/data/', auth='connector_bi', type='json', cors='*', methods=['POST'])
    def field_data(self, fields, model, limit, page, domain):
        page = int(page)
        limit = int(limit)
        headers = {'Content-Type': 'application/json'}
        return self.get_query(fields, model, domain, limit, page)
        # return json.dumps(result, default=self.datetime_serializer)

    def get_query(self, fields, model, domain, limit=10, page=1, order=None):
        results = []
        total = 0
        if order is None:
            order = ['id ASC']
        order = ', '.join(order)
        offset = (page - 1) * limit
        table = model['model'].replace('.', '_')
        total = request.env[model['model']].search_count(domain)
        search = request.env[model['model']].search(domain, order=order, offset=offset, limit=limit)

        field_names = []
        field_names_related = []
        for field in fields:
            if 'related_field' in field and field['related_field']:
                field_names_related.append({'related': field['related_field'], 'field': field['name']})
            else:
                field_names.append(field['name'])

        field_descriptions = [field['field_description'] for field in fields]
        for row in search:
            for field in row.read(field_names):
                if field_names_related:
                    for field_related in field_names_related:
                        related_field = getattr(row, field_related['related'])
                        try:
                            read_data = related_field.read([field_related['field']])[0]
                            field[field_related['field']] = read_data[field_related['field']]
                        except IndexError:
                            field[field_related['field']] = None
                results.append(field)

        return {'result': results, 'total': total}

    def datetime_serializer(self, object):
        if isinstance(object, datetime) | isinstance(object, date):
            return object.__str__()

    @http.route('/api_bi/chart/', auth='connector_bi', type='json', cors='*', methods=['POST'])
    def chart_data_column(self, fields, model, dimension, measure, chart_type):
        fields = [field for field in fields if field['id'] in [dimension, measure]]
        headers = {'Content-Type': 'application/json'}
        result = self.get_query_chart(fields, model, dimension, measure)
        result['type'] = chart_type
        return result

    def get_query_chart(self, fields, model, dimension, measure, order=None):
        if order is None:
            order = ['id ASC']
        order = ', '.join(order)
        search = request.env[model['model']].search([], order=order, limit=0)

        field_names = [field['name'] for field in fields]
        field_descriptions = [field['field_description'] for field in fields]
        results = {}
        dimension = [field for field in fields if field['id'] == dimension][0]
        measure = [field for field in fields if field['id'] == measure][0]
        for row in search:
            for record in row.read(field_names):
                dimension_value = record[dimension['name']] if not isinstance(record[dimension['name']], tuple) \
                    else record[dimension['name']][1]
                if dimension_value not in results:
                    results[dimension_value] = 0
                results[dimension_value] += record[measure['name']]

        results = [{'label': dimension, 'value': results[dimension]} for dimension in results]
        title = "{}: {} per {}".format(model['name'], measure['field_description'], dimension['field_description'])
        return {'result': results, 'axis_x_name': dimension['field_description'],
                'axis_y_name': measure['field_description'], 'title': title}

    @http.route('/api_bi/query/chart/pie2d/', auth='public', type='http', cors='*', methods=['POST'], csrf=False)
    def chart_data_pie(self, fields, model, dimension, measure, type):
        return self.chart_data_column(fields, model, dimension, measure, type)

    @http.route('/api_bi/query/chart/line/', auth='public', type='http', cors='*', methods=['POST'], csrf=False)
    def chart_data_line(self, fields, model, dimension, measure, type):
        return self.chart_data_column(fields, model, dimension, measure, type)

    @http.route('/api_bi/query/chart/spline/', auth='public', type='http', cors='*', methods=['POST'], csrf=False)
    def chart_data_spline(self, fields, model, dimension, measure, type):
        return self.chart_data_column(fields, model, dimension, measure, type)

    @http.route('/api_bi/query/chart/area2d/', auth='public', type='http', cors='*', methods=['POST'], csrf=False)
    def chart_data_area2d(self, fields, model, dimension, measure, type):
        return self.chart_data_column(fields, model, dimension, measure, type)

    @http.route('/api_bi/table/', auth='connector_bi', type='json', cors='*', methods=['POST'])
    def table_data(self, fields, model, dimensions, measures, options, extra_fields, domain):
        headers = {'Content-Type': 'application/json'}
        result = self.get_query_table(fields, model, dimensions, measures, options, extra_fields, domain)
        return result

    def get_query_table(self, fields, model, dimensions, measures, options, extra_fields, domain, order=None):
        if order is None:
            order = ['id ASC']
        order = ', '.join(order)
        domain = [tuple(arg) for arg in domain]
        search = request.env[model['model']].search(domain, order=order, limit=0)

        field_names = []
        field_names_related = []
        for field in fields:
            if 'related_field' in field and field['related_field']:
                field_names_related.append({'related': field['related_field'], 'field': field['name']})
            else:
                field_names.append(field['name'])
        field_descriptions = [field['field_description'] for field in fields]
        dimensions = [field for field in fields if field['id'] in dimensions]
        measures = [field for field in fields if field['id'] in measures]
        try:
            group_column = [field for field in dimensions if str(field['id']) in options and
                            options[str(field['id'])]['type'] == 'column'][0]
        except IndexError:
            group_column = None
        try:
            group_row = [field for field in dimensions if str(field['id']) in options and
                         options[str(field['id'])]['type'] == 'row'][0]
        except IndexError:
            group_row = None

        headers = []
        if group_row:
            headers.append({'text': group_row['field_description'], 'name': group_row['name']})
            if not group_column and len(measures) > 0:
                headers.append({'text': measures[0]['field_description'], 'name': measures[0]['name']})
        conversion = None
        if extra_fields and any(i in extra_fields for i in ['total_column_usd', 'total_row_usd']):
            conversion = 'USD'

        headers, results, results_conversion = self.get_values(field_names, group_column, group_row, headers, measures,
                                                               options, search, conversion)

        data = self.get_rows(group_column, group_row, measures, results)
        data_conversion = self.get_rows(group_column, group_row, measures, results_conversion)

        if extra_fields:
            if 'total_column' in extra_fields and group_row:
                new_row = self.add_total_column(data, group_row, headers, 'Total')
                data.append(new_row)
            if 'total_column_usd' in extra_fields and group_row:
                new_row = self.add_total_column(data_conversion, group_row, headers, 'Total USD')
                data.append(new_row)
                data_conversion.append(new_row)
            if 'total_row' in extra_fields and group_column:
                data = self.add_total_row(data, group_row, headers, 'Total', 'total')
            if 'total_row_usd' in extra_fields and group_column:
                if 'total_column_usd' not in extra_fields:
                    new_row = self.add_total_column(data_conversion, group_row, headers, 'Total USD')
                    data_conversion.append(new_row)
                data = self.add_total_row(data_conversion, group_row, headers, 'Total USD', 'total_usd', data)

        return {'result': data, 'headers': headers, 'total': len(data)}

    def add_total_row(self, data, group_row, headers, text, name, data_target=None):
        headers.append({'text': text, 'name': name})
        data_target = data if not data_target else data_target
        for index, row in enumerate(data):
            total = 0
            for value_row in row:
                if value_row != 'id' and (not group_row or value_row != group_row['name']):
                    total += row[value_row] \
                        if isinstance(row[value_row], int) or isinstance(row[value_row], float) else 0
            data_target[index][name] = total
        return data_target

    def add_total_column(self, data, group_row, headers, text):
        new_row = {'id': random.randint(0, 1000000)}
        for value in headers:
            if value['name'] == group_row['name']:
                new_row[value['name']] = text
            else:
                new_row[value['name']] = 0
        for index, row in enumerate(data):
            for value_row in row:
                if value_row not in [group_row['name'], 'id', 'total']:
                    new_row[value_row] += row[value_row] \
                        if isinstance(row[value_row], int) or isinstance(row[value_row], float) else 0
        return new_row

    def get_rows(self, group_column, group_row, measures, results):
        data = []
        row = {}
        if group_row:
            for key in results:
                row = {}
                row[group_row['name']] = key
                if group_column:
                    for column in results[key]:
                        row[column] = results[key][column]
                elif len(measures) > 0:
                    row[measures[0]['name']] = results[key]
                row['id'] = random.randint(0, 1000000)
                data.append(row)
        elif group_column:
            for key in results:
                row[key] = results[key]
            row['id'] = random.randint(0, 1000000)
            data.append(row)
        else:
            for key in results:
                row[key] = results[key]
            row['id'] = random.randint(0, 1000000)
            data.append(row)
        return data

    def get_values(self, field_names, group_column, group_row, headers, measures, options, search, conversion=None):
        results = {}
        results_conversion = {}
        for row in search:
            for record in row.read(field_names):
                # column
                if group_column:
                    if group_column['related_field']:
                        related_field = getattr(row, group_column['related_field'])
                        try:
                            read_data = related_field.read([group_column['name']])[0]
                            group_column_value = read_data[group_column['name']]
                        except IndexError:
                            group_column_value = ''
                    else:
                        group_column_value = record[group_column['name']] if not isinstance(
                            record[group_column['name']],
                            tuple) \
                            else record[group_column['name']][1]
                    if group_column_value and 'group_type' in options[str(group_column['id'])]:
                        if group_column['type'] in ['datetime', 'date']:
                            if options[str(group_column['id'])]['group_type'] == 'day':
                                group_column_value = group_column_value.strftime("%d")
                            if options[str(group_column['id'])]['group_type'] == 'month':
                                group_column_value = group_column_value.strftime("%B")
                            if options[str(group_column['id'])]['group_type'] == 'year':
                                group_column_value = group_column_value.strftime("%Y")
                if group_row:
                    if group_row['related_field']:
                        related_field = getattr(row, group_row['related_field'])
                        try:
                            read_data = related_field.read([group_row['name']])[0]
                            group_row_value = read_data[group_row['name']] \
                                if not isinstance(read_data[group_row['name']], tuple) \
                                else read_data[group_row['name']][1]
                        except IndexError:
                            group_row_value = ''
                    else:
                        group_row_value = record[group_row['name']] if not isinstance(
                            record[group_row['name']],
                            tuple) \
                            else record[group_row['name']][1]

                measure_value = 0
                measure_value_usd = 0
                if len(measures) > 0:
                    measure = measures[0]
                    measure_value = record[measure['name']]
                    if conversion:
                        # row.create_date
                        if row.currency_id.name != 'USD':
                            company_currency = row.company_id.currency_id.name
                            if company_currency != 'USD':
                                currency = 'USD'
                            else:
                                currency = company_currency
                            sql = """
                                    SELECT rate FROM res_currency RC 
                                        JOIN res_currency_rate RCR ON rc.id = rcr.currency_id 
                                        WHERE rc.name = %s AND rcr.company_id = %s
                                        ORDER BY abs(rcr.name - %s::DATE) 
                                        limit 1
                            """
                            request.cr.execute(sql, (currency, row.company_id.id, row.create_date))
                            rate = request.cr.fetchone()[0]
                            if company_currency != 'USD':
                                measure_value_usd = rate * measure_value
                            else:
                                measure_value_usd = measure_value / rate

                        else:
                            measure_value_usd = measure_value

                if group_row:
                    if group_column:
                        if group_row_value not in results:
                            results[group_row_value] = {}
                            results_conversion[group_row_value] = {}
                        if group_column_value not in results[group_row_value]:
                            results[group_row_value][group_column_value] = 0
                            results_conversion[group_row_value][group_column_value] = 0
                            if {'text': group_column_value, 'name': group_column_value} not in headers:
                                headers.append({'text': group_column_value, 'name': group_column_value})
                        else:
                            results[group_row_value][group_column_value] += measure_value \
                                if (isinstance(measure_value, int) or isinstance(measure_value, float)) else 0
                            results_conversion[group_row_value][group_column_value] += measure_value_usd \
                                if (isinstance(measure_value_usd, int) or isinstance(measure_value_usd, float)) else 0
                    else:
                        if group_row_value not in results:
                            results[group_row_value] = 0
                            results_conversion[group_row_value] = 0
                        results[group_row_value] += measure_value if (isinstance(measure_value, int) or
                                                                      isinstance(measure_value, float)) else 0
                        results_conversion[group_row_value] += measure_value_usd if (isinstance(measure_value_usd, int) or
                                                                                     isinstance(measure_value_usd,
                                                                                                float)) else 0
                elif group_column:
                    if group_column_value not in results:
                        results[group_column_value] = 0
                        results_conversion[group_column_value] = 0
                        headers.append({'text': group_column_value, 'name': group_column_value})
                    else:
                        results[group_column_value] += measure_value \
                            if (isinstance(measure_value, int) or isinstance(measure_value, float)) else 0
                        results_conversion[group_column_value] += measure_value_usd \
                            if (isinstance(measure_value_usd, int) or isinstance(measure_value_usd, float)) else 0
                else:
                    if measure['name'] not in results:
                        results[measure['name']] = 0
                        results_conversion[measure['name']] = 0
                        headers.append({'text': measure['field_description'], 'name': measure['name']})
                    results[measure['name']] += measure_value
                    results_conversion[measure['name']] += measure_value_usd
        return headers, results, results_conversion
