# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo.http import request


def currency_rate_table():
    return """
    SELECT DISTINCT ON (currency_id)
        currency_id, rate
    FROM res_currency_rate curr_rate
    WHERE create_date < DATE %(currency_date)s
    ORDER BY currency_id, create_date DESC
    """


def get_dates_datapoints(dates):
    return "VALUES " + ','.join(f"(DATE %(date_{n})s)" for n in range(len(dates))), {f'date_{n}': date for n, date in enumerate(dates)}


def get_churn_dates_datapoints(dates):
    return "VALUES " + ','.join(f"(DATE %(date_churnA_{n})s, DATE %(date_churnB_{n})s)" for n in range(len(dates))), \
           {**{f'date_churnA_{n}': date + relativedelta(months=-1) for n, date in enumerate(dates)}, **{f'date_churnB_{n}': date for n, date in enumerate(dates)}}


def make_filters_query(filters):
    join = where = ""
    args = {}

    if filters.get('template_ids'):
        join += "\nJOIN sale_order so ON aml.subscription_id = so.id"
        where += "\nAND so.sale_order_template_id IN %(template_ids)s"
        args['template_ids'] = tuple(filters['template_ids'])

    if filters.get('sale_team_ids'):
        join += "\nJOIN crm_team crm ON am.team_id = crm.id"
        where += "\nAND crm.id IN %(team_ids)s"
        args['team_ids'] = tuple(filters['sale_team_ids'])

    if filters.get('company_ids'):
        where += """\nAND am.company_id IN %(company_ids)s
                 AND aml.company_id IN %(company_ids)s"""
        args['company_ids'] = tuple(filters['company_ids'])

    return join, where, args


def compute_nb_contracts_batch(dates, filters):
    join, where, query_args = make_filters_query(filters)
    dates_datapoints, date_args = get_dates_datapoints(dates)
    query_args = {**query_args, **date_args}

    query = f"""
    WITH 
        dates(date) AS ({dates_datapoints}),
        subscription AS (
            SELECT 
                aml.subscription_id, 
                MIN(aml.subscription_start_date) AS start_date, 
                MAX(aml.subscription_end_date) AS end_date
    
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            {join}
    
            WHERE   am.move_type IN ('out_invoice', 'out_refund')
            AND     am.state NOT IN ('draft', 'cancel')
            AND     aml.subscription_id IS NOT NULL
            AND NOT aml.subscription_start_date > %(end_date)s
            AND NOT aml.subscription_end_date < %(start_date)s
            {where}
            
            GROUP BY aml.subscription_id
        )

    SELECT date, running_value AS value
    FROM (
        SELECT SUM (value) OVER (ORDER BY date, value DESC) AS running_value, date, value 
        FROM (
            -- New Subscription count as +1
            SELECT start_date AS date, 1 AS value
            FROM subscription
            UNION ALL
            -- Expiring subscription count as -1
            SELECT end_date AS date, -1 AS value
            FROM subscription
            UNION ALL
            -- Interesting dates
            SELECT date, 0 AS value 
            FROM dates
        ) a
    ) b    
    WHERE value = 0  
    """
    query_args.update(
        start_date=dates[0],
        end_date=dates[-1],
    )

    request.cr.execute(query, query_args)
    return request.cr.dictfetchall()


def compute_logo_churn_batch(dates, filters):
    """ Logo churn represent percentage of customer that were present one month ago and that are still present now
    """
    join, where, query_args = make_filters_query(filters)
    dates_datapoints, date_args = get_dates_datapoints(dates)
    churn_dates_datapoints, churn_date_args = get_churn_dates_datapoints(dates)
    query_args = {**query_args, **date_args, **churn_date_args}

    query = f"""
    WITH 
        dates(date) AS ({dates_datapoints}),
        churn_dates(date_start, date_end) AS ({churn_dates_datapoints}),
        subscription AS (
            SELECT 
                aml.subscription_id, 
                MIN(aml.subscription_start_date) as start_date, 
                MAX(aml.subscription_end_date) as end_date
    
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            {join}
    
            WHERE   am.move_type IN ('out_invoice', 'out_refund')
            AND     am.state NOT IN ('draft', 'cancel')
            AND     aml.subscription_id IS NOT NULL
            AND NOT aml.subscription_start_date > %(end_date)s
            AND NOT aml.subscription_end_date < %(start_date)s
            {where}
            
            GROUP BY aml.subscription_id
        ),
        
        running AS (
            SELECT 
                SUM (new_value) OVER (ORDER BY date, new_value DESC, exp_value) AS new_running_value,
                SUM (exp_value) OVER (ORDER BY date, new_value DESC, exp_value) AS exp_running_value,
                date, date_after, new_value, exp_value
            FROM (
                -- Interesting dates
                SELECT  date_start AS date, date_end AS date_after, 0 AS new_value, 0 AS exp_value 
                FROM    churn_dates
                UNION ALL
                SELECT  date, NULL AS date_after, 0 AS new_value, 0 AS exp_value 
                FROM    dates
                WHERE   date NOT IN (SELECT date_start FROM churn_dates)
                UNION ALL
                -- Allow to count the subscription that have started before the date
                SELECT  start_date AS date, NULL AS date_after, 1 AS new_value, 0 AS exp_value
                FROM    subscription
                WHERE end_date - interval '1 months - 1 days' >= start_date -- Subscription that last less than a month are useless for this
                UNION ALL
                -- Allow to count the subscription that have started before the date
                SELECT  end_date AS date, NULL AS date_after, 0 AS new_value, 1 AS exp_value
                FROM    subscription
                WHERE end_date - interval '1 months - 1 days' >= start_date -- Subscription that last less than a month are useless for this
            ) temp
        )
        
    SELECT  old_running.date_after AS date,
            CASE WHEN old_running.new_running_value = old_running.exp_running_value THEN 0
            ELSE 100 - 100*(old_running.new_running_value - new_running.exp_running_value) / (old_running.new_running_value - old_running.exp_running_value) END
            AS value
    
    FROM running AS old_running
    LEFT JOIN running AS new_running ON old_running.date_after = new_running.date
    
    -- We only want interesting date
    WHERE   new_running.new_value = 0
    AND     new_running.exp_value = 0
    """

    query_args.update(
        start_date=dates[0],
        end_date=dates[-1],
    )

    request.cr.execute(query, query_args)
    return request.cr.dictfetchall()

def compute_net_revenue_batch(dates, filters):
    join, where, query_args = make_filters_query(filters)
    dates_datapoints, date_args = get_dates_datapoints(dates)
    query_args = {**query_args, **date_args}

    query = f"""
        WITH 
            dates(date) AS ({dates_datapoints}),
            currency_rate AS ({currency_rate_table()}),
            subscription AS (
                SELECT 
                    aml.subscription_id, 
                    aml.subscription_start_date, 
                    aml.subscription_end_date,
                    SUM(aml.price_subtotal) * COALESCE(cr.rate, 1) as subtotal                
    
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                LEFT JOIN currency_rate cr ON cr.currency_id = aml.currency_id
                {join}
    
                WHERE   am.move_type IN ('out_invoice', 'out_refund')
                AND     am.state NOT IN ('draft', 'cancel')
                AND     aml.subscription_id IS NOT NULL
                AND NOT aml.subscription_start_date > %(end_date)s
                AND NOT aml.subscription_end_date < %(start_date)s
                AND     aml.price_subtotal > 0      -- We only take the revenue (and null revenue are useless)
                {where}
    
                GROUP BY aml.subscription_id, 
                        aml.subscription_start_date, 
                        aml.subscription_end_date,
                        cr.rate
            )
        
        SELECT date, running_value - LAG(running_value, 1, 0.0) OVER (ORDER BY date) AS value
        FROM (
            SELECT SUM (value) OVER (ORDER BY date, value DESC) AS running_value, date, value 
            FROM (
                -- New Subscription count as + net revenue
                SELECT subscription_start_date AS date, subtotal AS value
                FROM subscription
                UNION ALL
                -- Interesting dates
                SELECT date, 0 AS value 
                FROM dates
            ) a
        ) b    
        WHERE value = 0  
        """

    query_args.update(
        start_date=dates[0],
        end_date=dates[-1],
        currency_date=dates[-1],
    )

    request.cr.execute(query, query_args)
    return request.cr.dictfetchall()


def compute_nrr_batch(dates, filters):
    join, where, query_args = make_filters_query(filters)
    dates_datapoints, date_args = get_dates_datapoints(dates)
    query_args = {**query_args, **date_args}

    query = f"""
        WITH 
            currency_rate AS ({currency_rate_table()}),
            dates(date) AS ({dates_datapoints}),
            subscription AS (
                SELECT 
                    aml.subscription_id, 
                    am.invoice_date,
                    SUM(aml.price_subtotal) * COALESCE(cr.rate, 1) as subtotal
    
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                LEFT JOIN currency_rate cr ON cr.currency_id = aml.currency_id
                {join}
    
                WHERE   am.move_type IN ('out_invoice', 'out_refund')
                AND     am.state NOT IN ('draft', 'cancel')
                AND     aml.subscription_id IS NOT NULL
                AND     aml.subscription_start_date IS NULL
                AND     aml.display_type = 'product'
                AND     aml.price_subtotal > 0      -- We only take the revenue (and null revenue are useless)
                {where}
    
                GROUP BY aml.subscription_id, 
                        am.invoice_date,
                        cr.rate
            )

        SELECT date, running_value - LAG(running_value, 1, 0.0) OVER (ORDER BY date) AS value
        FROM (
            SELECT SUM (value) OVER (ORDER BY date, value DESC) AS running_value, date, value 
            FROM (
                -- New Subscription count as + net revenue
                SELECT invoice_date AS date, subtotal AS value
                FROM subscription
                UNION ALL
                -- Interesting dates
                SELECT date, 0 AS value 
                FROM dates
            ) a
        ) b    
        WHERE value = 0  
        """

    query_args.update(
        start_date=dates[0],
        end_date=dates[-1],
        currency_date=dates[-1],
    )

    request.cr.execute(query, query_args)
    return request.cr.dictfetchall()

def compute_mrr_batch(dates, filters):
    join, where, query_args = make_filters_query(filters)
    dates_datapoints, date_args = get_dates_datapoints(dates)
    query_args = {**query_args, **date_args}

    query = f"""
        WITH 
            currency_rate AS ({currency_rate_table()}),
            dates(date) AS ({dates_datapoints}),
            subscription AS (
                SELECT 
                    aml.subscription_id, 
                    aml.subscription_start_date, 
                    aml.subscription_end_date,
                    SUM(aml.subscription_mrr) * COALESCE(cr.rate, 1) as subtotal

                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                LEFT JOIN currency_rate cr ON cr.currency_id = aml.currency_id
                {join}
                
                WHERE   am.move_type IN ('out_invoice', 'out_refund')
                AND     am.state NOT IN ('draft', 'cancel')
                AND     aml.subscription_id IS NOT NULL
                AND NOT aml.subscription_start_date > %(end_date)s
                AND NOT aml.subscription_end_date < %(start_date)s
                AND     aml.subscription_mrr != 0      -- We only take useful revenues (and null revenue are useless)
                {where}
                
                GROUP BY    
                    aml.subscription_id, 
                    aml.subscription_start_date, 
                    aml.subscription_end_date,
                    cr.rate
            )
            
        SELECT date, running_value AS value
        FROM (
            SELECT SUM (value) OVER (ORDER BY date, value DESC) AS running_value, date, value 
            FROM (
                -- New Subscription count as + MRR
                SELECT subscription_start_date AS date, subtotal AS value
                FROM subscription
                UNION ALL
                -- New Subscription count as - MRR
                SELECT subscription_end_date AS date, -subtotal AS value
                FROM subscription
                UNION ALL
                -- Interesting dates
                SELECT date, 0 AS value 
                FROM dates
            ) a
        ) b    
        WHERE value = 0  
        """

    query_args.update(
        start_date=dates[0],
        end_date=dates[-1],
        currency_date=dates[-1],
    )

    request.cr.execute(query, query_args)
    return request.cr.dictfetchall()


def compute_arpu_batch(dates, filters):

    nb_contracts = compute_nb_contracts_batch(dates, filters)
    mrrs = compute_mrr_batch(dates, filters)
    # TODO compute without other function call
    return [{'date':mrr['date'], 'value':mrr['value']/nb_contract['value'] if nb_contract['value'] else 0} for mrr, nb_contract in zip(mrrs, nb_contracts)]


def compute_arr_batch(dates, filters):
    mrrs = compute_mrr_batch(dates, filters)
    for mrr in mrrs:
        mrr['value'] *= 12
    return mrrs


def compute_ltv_batch(dates, filters):
    arpus = compute_arpu_batch(dates, filters)
    logos = compute_logo_churn_batch(dates, filters)
    return [{'date':arpu['date'], 'value':arpu['value']/logo['value'] if logo['value'] else 0} for arpu, logo in zip(arpus, logos)]


def compute_revenue_churn_batch(dates, filters):
    """ revenue churn represent percentage of revenue that was present one month ago and that is still present now
    """
    join, where, query_args = make_filters_query(filters)
    dates_datapoints, date_args = get_dates_datapoints(dates)
    churn_dates_datapoints, churn_date_args = get_churn_dates_datapoints(dates)
    query_args = {**query_args, **date_args, **churn_date_args}

    query = f"""
            WITH 
                currency_rate AS ({currency_rate_table()}),
                dates(date) AS ({dates_datapoints}),
                churn_dates(date_start, date_end) AS ({churn_dates_datapoints}),
                subscription AS (
                    SELECT 
                        aml.subscription_id, 
                        aml.subscription_start_date as start_date, 
                        aml.subscription_end_date as end_date,
                        SUM(aml.subscription_mrr) * COALESCE(cr.rate, 1) as subtotal

                    FROM account_move_line aml
                    JOIN account_move am ON am.id = aml.move_id
                    LEFT JOIN currency_rate cr ON cr.currency_id = aml.currency_id
                    {join}

                    WHERE   am.move_type IN ('out_invoice', 'out_refund')
                    AND     am.state NOT IN ('draft', 'cancel')
                    AND     aml.subscription_id IS NOT NULL
                    AND NOT aml.subscription_start_date > %(end_date)s
                    AND NOT aml.subscription_end_date < %(start_date)s
                    AND     aml.subscription_mrr != 0      -- We only take useful revenues (and null revenue are useless)
                    {where}

                    GROUP BY    
                        aml.subscription_id, 
                        aml.subscription_start_date, 
                        aml.subscription_end_date,
                        cr.rate
                ),

                running AS (
                    SELECT 
                        SUM (new_value) OVER (ORDER BY date, new_value DESC, exp_value) AS new_running_value,
                        SUM (exp_value) OVER (ORDER BY date, new_value DESC, exp_value) AS exp_running_value,
                        date, date_after, new_value, exp_value
                    FROM (
                        -- Interesting dates
                        SELECT  date_start AS date, date_end AS date_after, 0 AS new_value, 0 AS exp_value 
                        FROM    churn_dates
                        UNION ALL
                        SELECT  date, NULL AS date_after, 0 AS new_value, 0 AS exp_value
                        FROM    dates
                        WHERE   date NOT IN (SELECT date_start FROM churn_dates)
                        UNION ALL
                        -- Allow to count the subscription that have started before the date
                        SELECT  start_date AS date, NULL AS date_after, subtotal AS new_value, 0 AS exp_value
                        FROM    subscription
                        WHERE   end_date - interval '1 months - 1 days' >= start_date -- Subscription that last less than a month are useless for this
                        UNION ALL
                        -- Allow to count the subscription that have started before the date
                        SELECT  end_date AS date, NULL AS date_after, 0 AS new_value, subtotal AS exp_value
                        FROM    subscription
                        WHERE   end_date - interval '1 months - 1 days' >= start_date -- Subscription that last less than a month are useless for this
                    ) temp
                )

            SELECT  old_running.date_after AS date,
                CASE WHEN old_running.new_running_value = old_running.exp_running_value THEN 0
                ELSE 100 - 100*(old_running.new_running_value - new_running.exp_running_value) / (old_running.new_running_value - old_running.exp_running_value) END
                AS value
            
            FROM running AS old_running
            LEFT JOIN running AS new_running ON old_running.date_after = new_running.date

            -- We only want interesting date
            WHERE   new_running.new_value = 0
            AND     new_running.exp_value = 0
    """

    query_args.update(
        start_date=dates[0],
        end_date=dates[-1],
        currency_date=dates[-1],
    )

    request.cr.execute(query, query_args)
    return request.cr.dictfetchall()
