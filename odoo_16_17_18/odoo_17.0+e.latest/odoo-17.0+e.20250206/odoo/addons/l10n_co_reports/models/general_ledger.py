from odoo import api, models, _


class GeneralLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
        if not options.get('l10n_co_reports_groupby_partner_id'):
            return super()._dynamic_lines_generator(report, options, all_column_groups_expression_totals, warnings)

        lines_groupby_account, total_line = self._l10n_co_reports_get_lines_group_by_account_and_partner(report, options)

        # Order lines by account code
        sorted_lines = [
            line
            for account_key in sorted(lines_groupby_account, key=lambda account: account.code)
            for line in lines_groupby_account[account_key]
        ]
        sorted_lines.append(total_line)

        return [(0, line) for line in sorted_lines]

    def _l10n_co_reports_get_lines_group_by_account_and_partner(self, report, options):
        # Returns
        #   - A dict representing the lines that need to be added to the report, grouped by account
        #   - The final line with the total amounts
        # Note: All moves without partner are grouped into a single line at the end of each list

        def custom_sort_key(line):
            # Order lines alphabetically by partner name, with the parent line on top and the line without partner at the bottom
            custom_partner_id = line['l10n_co_partner_id']
            custom_partner_id = 0 if custom_partner_id else 1
            return not line['is_parent'], custom_partner_id, line['l10n_co_partner_name']

        lines_groupby_account = {}
        for (account, partner_id), column_group_results in self._l10n_co_reports_query_values(report, options):
            eval_dict = {}
            partner_name = ''
            partner_vat = ''
            for column_group_key, results in column_group_results.items():
                account_sum = results.get('sum', {})
                account_un_earn = results.get('unaffected_earnings', {})

                if not partner_name:
                    partner_name = account_sum.get('partner_name', '') or account_un_earn.get('partner_name', '')

                if not partner_vat:
                    partner_vat = account_sum.get('partner_vat', '') or account_un_earn.get('partner_vat', '')

                eval_dict[column_group_key] = {
                    'amount_currency': account_sum.get('amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0),
                    'debit': account_sum.get('debit', 0.0) + account_un_earn.get('debit', 0.0),
                    'credit': account_sum.get('credit', 0.0) + account_un_earn.get('credit', 0.0),
                    'balance': account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0),
                }

            lines_groupby_account.setdefault(account, []).append(
                self._l10n_co_reports_get_account_title_line(report, options, account, partner_id, partner_name, partner_vat, eval_dict)
            )

        total_amounts = [0] * len(options['columns'])

        for account, partner_lines in lines_groupby_account.items():
            parent_line_col_values = [
                sum(partner_line['columns'][i]['no_format'] or 0.0 for partner_line in partner_lines)
                for i in range(len(options['columns']))
            ]

            parent_line = self._l10n_co_reports_get_empty_parent_line(report, options, account, parent_line_col_values)
            parent_line['id'] = report._get_generic_line_id('account.account', account.id)

            for partner_line in partner_lines:
                partner_line['parent_id'] = parent_line['id']

            total_amounts = [x + y for x, y in zip(total_amounts, parent_line_col_values)]

            partner_lines.append(parent_line)
            partner_lines.sort(key=custom_sort_key)

        total_line = self._l10n_co_reports_get_total_line(report, options, total_amounts)

        return lines_groupby_account, total_line

    @api.model
    def _l10n_co_reports_get_empty_parent_line(self, report, options, account, parent_line_col_values):
        line_columns = []
        for i, column in enumerate(options['columns']):
            if column['expression_label'] == 'partner_name':
                line_columns.append({'name': '', 'no_format': 0.0, 'class': ''})
                continue
            if column['expression_label'] == 'partner_vat':
                line_columns.append({'name': '', 'no_format': 0.0, 'class': ''})
                continue

            col_value = parent_line_col_values[i]
            formatted_value = report.format_value(options, col_value, figure_type=column['figure_type'], blank_if_zero=True)

            line_columns.append({
                'name': formatted_value,
                'no_format': col_value,
                'class': 'number',
            })

        return {
            'name': f'{account.code} {account.name}',
            'search_key': account.code,
            'columns': line_columns,
            'level': 1,
            'unfoldable': False,
            'unfolded': False,
            'l10n_co_partner_name': '',
            'l10n_co_partner_id': '',
            'is_parent': True,
        }

    @api.model
    def _l10n_co_reports_get_account_title_line(self, report, options, account, partner_id, partner_name, partner_vat, eval_dict):
        line_columns = []
        for column in options['columns']:
            if column['expression_label'] == 'partner_name':
                line_columns.append({
                    'name': partner_name if partner_id else _('(None)'),
                    'no_format': 0.0,
                })
                continue
            if column['expression_label'] == 'partner_vat':
                line_columns.append({
                    'name': partner_vat,
                    'no_format': 0.0,
                })
                continue

            col_value = eval_dict[column['column_group_key']].get(column['expression_label'])
            formatted_value = report.format_value(options, col_value, figure_type=column['figure_type'], blank_if_zero=True)

            line_columns.append({
                'name': formatted_value,
                'no_format': col_value,
                'class': 'number',
            })

        line_id = report._get_generic_line_id('res.partner', partner_id, markup='account_id:' + str(account.id))
        return {
            'id': line_id,
            'name': f'{account.code} {account.name}',
            'search_key': account.code,
            'columns': line_columns,
            'level': 3,
            'unfoldable': False,
            'unfolded': False,
            'l10n_co_partner_name': partner_name,
            'l10n_co_partner_id': partner_id,
            'is_parent': False,
        }

    @api.model
    def _l10n_co_reports_get_total_line(self, report, options, total_amounts):
        total_line_columns = []
        for i, column in enumerate(options['columns']):
            if column['expression_label'] in ('partner_name', 'partner_vat'):
                total_line_columns.append({})
                continue

            col_value = total_amounts[i]
            formatted_value = report.format_value(options, col_value, blank_if_zero=False, figure_type='monetary')
            total_line_columns.append({
                'name': formatted_value,
                'no_format': col_value,
                'class': 'number',
            })

        return {
            'id': report._get_generic_line_id(None, None, markup='total'),
            'name': _('Total'),
            'class': 'total',
            'level': 1,
            'columns': total_line_columns,
        }

    def _l10n_co_reports_query_values(self, report, options):
        accounts_partners_keys = set()
        accounts_partners_map = {}
        companies_map = {}  # Changed from companies_partners_map

        aml_query, aml_params = self._l10n_co_reports_get_query_amls(report, options)
        self._cr.execute(aml_query, aml_params)

        for res in self._cr.dictfetchall():
            column_group_key = res['column_group_key']
            key = res['key']
            partner_id = res['partner_id']
            res['partner_vat'] = res['partner_vat'] or ''

            if key == 'sum':
                if res['account_type'] == 'equity_unaffected':
                    partner_id = None  # Remove partner details for unaffected earnings
                    res['partner_vat'] = ''

                account_id = res['groupby']
                groupby_key = (account_id, partner_id)
                accounts_partners_keys.add(groupby_key)
                accounts_partners_map.setdefault(groupby_key, {col_group_key: {} for col_group_key in options['column_groups']})
                accounts_partners_map[groupby_key][column_group_key][key] = res

            elif key == 'unaffected_earnings':
                company_id = res['groupby']
                companies_map.setdefault(company_id, {col_group_key: {} for col_group_key in options['column_groups']})
                companies_map[company_id][column_group_key] = res

        # Converts the unaffected earnings of the query to the proper unaffected account of the company.
        # The subgroup per partner no longer applies for unaffected earnings
        if companies_map:
            company_unaffected_account_map = {
                account.company_id.id: account
                for account in self.env['account.account'].search([
                    ('account_type', '=', 'equity_unaffected'),
                    ('company_id', 'in', list(companies_map.keys())),
                ])
            }
            for company_id, company_data in companies_map.items():
                account = company_unaffected_account_map[company_id]
                groupby_key = (account.id, None)  # Use None instead of partner_id
                accounts_partners_map.setdefault(groupby_key, {col_group_key: {} for col_group_key in options['column_groups']})
                for column_group_key in options['column_groups']:
                    if 'unaffected_earnings' not in accounts_partners_map[groupby_key][column_group_key]:
                        accounts_partners_map[groupby_key][column_group_key]['unaffected_earnings'] = companies_map[company_id][column_group_key]
                accounts_partners_keys.add(groupby_key)

        account_partner_keys = {(self.env['account.account'].browse(account_id), partner_id) for account_id, partner_id in accounts_partners_keys}
        return [(account_partner_key, accounts_partners_map[account_partner_key[0].id, account_partner_key[1]]) for account_partner_key in account_partner_keys]

    def _l10n_co_reports_get_query_amls(self, report, options):
        options_by_column_group = report._split_options_per_column_group(options)

        params = []
        queries = []

        # Create the currency table.
        # As the currency table is the same whatever the comparisons, create it only once.
        ct_query = report._get_query_currency_table(options)

        # ===============================================================
        # 1) Get sums for all (accounts, partners) existing combinations
        # ===============================================================
        for column_group_key, options_group in options_by_column_group.items():
            if not options.get('general_ledger_strict_range'):
                options_group = self._get_options_sum_balance(options_group)

            # Sum is computed including the initial balance of the accounts configured to do so, unless a special option key is used
            sum_date_scope = 'strict_range' if options_group.get('general_ledger_strict_range') else 'normal'
            query_domain = []

            if options.get('filter_search_bar'):
                query_domain.append(('account_id', 'ilike', options['filter_search_bar']))

            # Exclude move lines with P&L accounts from initial balance if they belong to a previous fiscal year
            if options_group.get('include_current_year_in_unaff_earnings'):
                query_domain += [('account_id.include_initial_balance', '=', True)]

            tables, where_clause, where_params = report._query_get(options_group, sum_date_scope, domain=query_domain)
            params.append(column_group_key)
            params += where_params
            queries.append(f"""
                        SELECT
                            account.id                                              AS groupby,
                            account.account_type                                    AS account_type,
                            partner.id                                              AS partner_id,
                            'sum'                                                   AS key,
                            MAX(account_move_line.date)                             AS max_date,
                            %s                                                      AS column_group_key,
                            COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                            SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                            SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                            SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                            account.code                                            AS account_code,
                            account.name                                            AS account_name,
                            partner.name                                            AS partner_name,
                            partner.vat                                             AS partner_vat
                        FROM {tables}
                        LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                        LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                        LEFT JOIN account_account account           ON account.id = account_move_line.account_id
                        LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                        LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
                        LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                        WHERE {where_clause}
                        GROUP BY account.id, partner.id
                    """)

            # ============================================
            # 2) Unaffected earnings.
            # ============================================
            if not options_group.get('general_ledger_strict_range'):
                # Apply to initial balance and end balance and only focus on unaffected earnings

                unaff_earnings_domain = [('account_id.include_initial_balance', '=', False)]

                # The period domain is expressed as:
                # [
                #   ('date' <= fiscalyear['date_from'] - 1),
                #   ('account_id.include_initial_balance', '=', False),
                # ]

                new_options = self._get_options_unaffected_earnings(options_group)
                tables, where_clause, where_params = report._query_get(new_options, 'strict_range', domain=unaff_earnings_domain)
                params.append(column_group_key)
                params += where_params
                queries.append(f"""
                            SELECT
                                company.id                                              AS groupby,
                                NULL                                                    AS account_type,
                                NULL                                                    AS partner_id,
                                'unaffected_earnings'                                   AS key,
                                NULL                                                    AS max_date,
                                %s                                                      AS column_group_key,
                                COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                                SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                                SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                                NULL                                                    AS account_code,
                                NULL                                                    AS account_name,
                                NULL                                                    AS partner_name,
                                NULL                                                    AS partner_vat
                            FROM {tables}
                            LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                            LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                            LEFT JOIN account_account account           ON account.id = account_move_line.account_id
                            LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                            LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
                            LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                            WHERE {where_clause}
                            GROUP BY company.id
                        """)

        return ' UNION ALL '.join(queries), params
