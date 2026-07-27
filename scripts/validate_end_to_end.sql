\set ON_ERROR_STOP on
\pset pager off

-- Run this file with psql, not through a generic SQL editor. Schema names can be
-- overridden with -v; the defaults match .env.example.
\if :{?raw_schema}
\else
  \set raw_schema raw
\endif

\if :{?staging_schema}
\else
  \set staging_schema staging
\endif

\if :{?marts_schema}
\else
  \set marts_schema marts
\endif

\echo
\echo 'Torgstat end-to-end validation'
\echo '================================'
\echo 'raw schema:     ' :raw_schema
\echo 'staging schema: ' :staging_schema
\echo 'marts schema:   ' :marts_schema

CREATE TEMP TABLE validation_results (
    check_order integer NOT NULL,
    layer text NOT NULL,
    check_name text NOT NULL,
    expected_value numeric,
    actual_value numeric,
    status text NOT NULL,
    details text NOT NULL
);

CREATE OR REPLACE FUNCTION pg_temp.add_equal_check(
    p_check_order integer,
    p_layer text,
    p_check_name text,
    p_expected_sql text,
    p_actual_sql text,
    p_details text
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_expected numeric;
    v_actual numeric;
BEGIN
    EXECUTE p_expected_sql INTO STRICT v_expected;
    EXECUTE p_actual_sql INTO STRICT v_actual;

    INSERT INTO validation_results (
        check_order,
        layer,
        check_name,
        expected_value,
        actual_value,
        status,
        details
    )
    VALUES (
        p_check_order,
        p_layer,
        p_check_name,
        v_expected,
        v_actual,
        CASE
            WHEN v_actual IS NOT DISTINCT FROM v_expected THEN 'PASS'
            ELSE 'FAIL'
        END,
        p_details
    );
END;
$$;

CREATE OR REPLACE FUNCTION pg_temp.add_zero_check(
    p_check_order integer,
    p_layer text,
    p_check_name text,
    p_violations_sql text,
    p_details text
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM pg_temp.add_equal_check(
        p_check_order,
        p_layer,
        p_check_name,
        'select 0::numeric',
        p_violations_sql,
        p_details
    );
END;
$$;

CREATE OR REPLACE FUNCTION pg_temp.add_minimum_check(
    p_check_order integer,
    p_layer text,
    p_check_name text,
    p_minimum numeric,
    p_actual_sql text,
    p_details text
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_actual numeric;
BEGIN
    EXECUTE p_actual_sql INTO STRICT v_actual;

    INSERT INTO validation_results (
        check_order,
        layer,
        check_name,
        expected_value,
        actual_value,
        status,
        details
    )
    VALUES (
        p_check_order,
        p_layer,
        p_check_name,
        p_minimum,
        v_actual,
        CASE WHEN v_actual >= p_minimum THEN 'PASS' ELSE 'FAIL' END,
        p_details
    );
END;
$$;

CREATE OR REPLACE FUNCTION pg_temp.add_key_set_check(
    p_check_order integer,
    p_layer text,
    p_check_name text,
    p_expected_keys_sql text,
    p_actual_keys_sql text,
    p_details text
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_differences numeric;
BEGIN
    EXECUTE format(
        $query$
        with expected as (%s),
        actual as (%s)
        select count(*)::numeric
        from expected
        full join actual using (record_key)
        where expected.record_key is null
           or actual.record_key is null
        $query$,
        p_expected_keys_sql,
        p_actual_keys_sql
    )
    INTO STRICT v_differences;

    INSERT INTO validation_results (
        check_order,
        layer,
        check_name,
        expected_value,
        actual_value,
        status,
        details
    )
    VALUES (
        p_check_order,
        p_layer,
        p_check_name,
        0,
        v_differences,
        CASE WHEN v_differences = 0 THEN 'PASS' ELSE 'FAIL' END,
        p_details
    );
END;
$$;

-- ---------------------------------------------------------------------------
-- 1. Generator and raw-load regression checks
-- ---------------------------------------------------------------------------

SELECT pg_temp.add_equal_check(
    10,
    'generator -> raw',
    'workspaces deterministic row count',
    'select 200::numeric',
    format('select count(*)::numeric from %I.workspaces', :'raw_schema'),
    'Seed-42 baseline documented in data/README.md.'
);

SELECT pg_temp.add_equal_check(
    11,
    'generator -> raw',
    'plans deterministic row count',
    'select 4::numeric',
    format('select count(*)::numeric from %I.plans', :'raw_schema'),
    'Seed-42 baseline documented in data/README.md.'
);

SELECT pg_temp.add_equal_check(
    12,
    'generator -> raw',
    'users deterministic row count',
    'select 2500::numeric',
    format('select count(*)::numeric from %I.users', :'raw_schema'),
    'Seed-42 baseline documented in data/README.md.'
);

SELECT pg_temp.add_equal_check(
    13,
    'generator -> raw',
    'sessions deterministic row count',
    'select 1297::numeric',
    format('select count(*)::numeric from %I.sessions', :'raw_schema'),
    'Seed-42 baseline documented in data/README.md.'
);

SELECT pg_temp.add_equal_check(
    14,
    'generator -> raw',
    'subscriptions deterministic row count',
    'select 180::numeric',
    format('select count(*)::numeric from %I.subscriptions', :'raw_schema'),
    'Seed-42 baseline documented in data/README.md.'
);

SELECT pg_temp.add_equal_check(
    15,
    'generator -> raw',
    'subscription plan history deterministic row count',
    'select 234::numeric',
    format(
        'select count(*)::numeric from %I.subscription_plan_history',
        :'raw_schema'
    ),
    'Seed-42 baseline documented in data/README.md.'
);

SELECT pg_temp.add_equal_check(
    16,
    'generator -> raw',
    'invoices deterministic row count',
    'select 935::numeric',
    format('select count(*)::numeric from %I.invoices', :'raw_schema'),
    'Seed-42 baseline documented in data/README.md.'
);

SELECT pg_temp.add_equal_check(
    17,
    'generator -> raw',
    'events deterministic row count',
    'select 5000::numeric',
    format('select count(*)::numeric from %I.events', :'raw_schema'),
    'Seed-42 baseline documented in data/README.md.'
);

SELECT pg_temp.add_minimum_check(
    18,
    'FX -> raw',
    'FX table is not empty',
    1,
    format('select count(*)::numeric from %I.fx_rates', :'raw_schema'),
    'A non-empty table is necessary but does not prove provider provenance.'
);

SELECT pg_temp.add_equal_check(
    19,
    'CSV -> raw',
    'one load batch across every raw table',
    'select 1::numeric',
    format(
        $query$
        select count(distinct load_batch_id)::numeric
        from (
            select _load_batch_id as load_batch_id from %1$I.workspaces
            union all select _load_batch_id from %1$I.plans
            union all select _load_batch_id from %1$I.users
            union all select _load_batch_id from %1$I.sessions
            union all select _load_batch_id from %1$I.subscriptions
            union all select _load_batch_id from %1$I.subscription_plan_history
            union all select _load_batch_id from %1$I.invoices
            union all select _load_batch_id from %1$I.events
            union all select _load_batch_id from %1$I.fx_rates
        ) as batches
        $query$,
        :'raw_schema'
    ),
    'Prevents a mixed raw snapshot assembled from different importer runs.'
);

SELECT pg_temp.add_equal_check(
    20,
    'CSV -> raw',
    'one load timestamp across every raw table',
    'select 1::numeric',
    format(
        $query$
        select count(distinct loaded_at_utc)::numeric
        from (
            select _loaded_at_utc as loaded_at_utc from %1$I.workspaces
            union all select _loaded_at_utc from %1$I.plans
            union all select _loaded_at_utc from %1$I.users
            union all select _loaded_at_utc from %1$I.sessions
            union all select _loaded_at_utc from %1$I.subscriptions
            union all select _loaded_at_utc from %1$I.subscription_plan_history
            union all select _loaded_at_utc from %1$I.invoices
            union all select _loaded_at_utc from %1$I.events
            union all select _loaded_at_utc from %1$I.fx_rates
        ) as load_times
        $query$,
        :'raw_schema'
    ),
    'All files are expected to be committed by one importer transaction.'
);

SELECT pg_temp.add_zero_check(
    21,
    'CSV -> raw',
    'source row numbers are complete and unique',
    format(
        $query$
        select count(*)::numeric
        from (
            select 'workspaces' as table_name
            from %1$I.workspaces
            having min(_source_row_number) <> 1
                or max(_source_row_number) <> count(*)
                or count(distinct _source_row_number) <> count(*)
            union all
            select 'plans'
            from %1$I.plans
            having min(_source_row_number) <> 1
                or max(_source_row_number) <> count(*)
                or count(distinct _source_row_number) <> count(*)
            union all
            select 'users'
            from %1$I.users
            having min(_source_row_number) <> 1
                or max(_source_row_number) <> count(*)
                or count(distinct _source_row_number) <> count(*)
            union all
            select 'sessions'
            from %1$I.sessions
            having min(_source_row_number) <> 1
                or max(_source_row_number) <> count(*)
                or count(distinct _source_row_number) <> count(*)
            union all
            select 'subscriptions'
            from %1$I.subscriptions
            having min(_source_row_number) <> 1
                or max(_source_row_number) <> count(*)
                or count(distinct _source_row_number) <> count(*)
            union all
            select 'subscription_plan_history'
            from %1$I.subscription_plan_history
            having min(_source_row_number) <> 1
                or max(_source_row_number) <> count(*)
                or count(distinct _source_row_number) <> count(*)
            union all
            select 'invoices'
            from %1$I.invoices
            having min(_source_row_number) <> 1
                or max(_source_row_number) <> count(*)
                or count(distinct _source_row_number) <> count(*)
            union all
            select 'events'
            from %1$I.events
            having min(_source_row_number) <> 1
                or max(_source_row_number) <> count(*)
                or count(distinct _source_row_number) <> count(*)
            union all
            select 'fx_rates'
            from %1$I.fx_rates
            having min(_source_row_number) <> 1
                or max(_source_row_number) <> count(*)
                or count(distinct _source_row_number) <> count(*)
        ) as invalid_tables
        $query$,
        :'raw_schema'
    ),
    'A failure means CSV-to-row lineage is incomplete or duplicated.'
);

SELECT pg_temp.add_zero_check(
    22,
    'CSV -> raw',
    'raw load metadata has no nulls',
    format(
        $query$
        select count(*)::numeric
        from (
            select _load_batch_id, _loaded_at_utc, _source_file, _source_row_number
            from %1$I.workspaces
            union all
            select _load_batch_id, _loaded_at_utc, _source_file, _source_row_number
            from %1$I.plans
            union all
            select _load_batch_id, _loaded_at_utc, _source_file, _source_row_number
            from %1$I.users
            union all
            select _load_batch_id, _loaded_at_utc, _source_file, _source_row_number
            from %1$I.sessions
            union all
            select _load_batch_id, _loaded_at_utc, _source_file, _source_row_number
            from %1$I.subscriptions
            union all
            select _load_batch_id, _loaded_at_utc, _source_file, _source_row_number
            from %1$I.subscription_plan_history
            union all
            select _load_batch_id, _loaded_at_utc, _source_file, _source_row_number
            from %1$I.invoices
            union all
            select _load_batch_id, _loaded_at_utc, _source_file, _source_row_number
            from %1$I.events
            union all
            select _load_batch_id, _loaded_at_utc, _source_file, _source_row_number
            from %1$I.fx_rates
        ) as raw_rows
        where _load_batch_id is null
           or _loaded_at_utc is null
           or _source_file is null
           or _source_row_number is null
        $query$,
        :'raw_schema'
    ),
    'The standalone reconciliation must not rely only on dbt not-null tests.'
);

-- ---------------------------------------------------------------------------
-- 2. Raw-to-staging row preservation
-- ---------------------------------------------------------------------------

SELECT pg_temp.add_equal_check(
    30, 'raw -> staging', 'workspaces row parity',
    format('select count(*)::numeric from %I.workspaces', :'raw_schema'),
    format('select count(*)::numeric from %I.stg_workspaces', :'staging_schema'),
    'Staging only types and normalizes this source.'
);

SELECT pg_temp.add_equal_check(
    31, 'raw -> staging', 'plans row parity',
    format('select count(*)::numeric from %I.plans', :'raw_schema'),
    format('select count(*)::numeric from %I.stg_plans', :'staging_schema'),
    'Staging only types and adds plan quality flags.'
);

SELECT pg_temp.add_equal_check(
    32, 'raw -> staging', 'users row parity',
    format('select count(*)::numeric from %I.users', :'raw_schema'),
    format('select count(*)::numeric from %I.stg_users', :'staging_schema'),
    'Invalid timestamps must be flagged, not silently discarded.'
);

SELECT pg_temp.add_equal_check(
    33, 'raw -> staging', 'sessions row parity',
    format('select count(*)::numeric from %I.sessions', :'raw_schema'),
    format('select count(*)::numeric from %I.stg_sessions', :'staging_schema'),
    'Staging only types and adds attribution flags.'
);

SELECT pg_temp.add_equal_check(
    34, 'raw -> staging', 'subscriptions row parity',
    format('select count(*)::numeric from %I.subscriptions', :'raw_schema'),
    format('select count(*)::numeric from %I.stg_subscriptions', :'staging_schema'),
    'Staging only types and adds lifecycle flags.'
);

SELECT pg_temp.add_equal_check(
    35, 'raw -> staging', 'subscription plan history row parity',
    format(
        'select count(*)::numeric from %I.subscription_plan_history',
        :'raw_schema'
    ),
    format(
        'select count(*)::numeric from %I.stg_subscription_plan_history',
        :'staging_schema'
    ),
    'Staging only types and adds history-period flags.'
);

SELECT pg_temp.add_equal_check(
    36, 'raw -> staging', 'invoices row parity',
    format('select count(*)::numeric from %I.invoices', :'raw_schema'),
    format('select count(*)::numeric from %I.stg_invoices', :'staging_schema'),
    'Bad invoices must remain traceable through explicit quality flags.'
);

SELECT pg_temp.add_equal_check(
    37, 'raw -> staging', 'events row parity',
    format('select count(*)::numeric from %I.events', :'raw_schema'),
    format('select count(*)::numeric from %I.stg_events', :'staging_schema'),
    'Duplicate payloads are retained and numbered.'
);

SELECT pg_temp.add_equal_check(
    38, 'raw -> staging', 'FX row parity',
    format('select count(*)::numeric from %I.fx_rates', :'raw_schema'),
    format('select count(*)::numeric from %I.stg_fx_rates', :'staging_schema'),
    'FX staging only types and normalizes the source.'
);

-- ---------------------------------------------------------------------------
-- 3. Staging-to-mart preservation and date-spine integrity
-- ---------------------------------------------------------------------------

SELECT pg_temp.add_equal_check(
    40, 'staging -> marts', 'dim_workspaces row parity',
    format('select count(*)::numeric from %I.stg_workspaces', :'staging_schema'),
    format('select count(*)::numeric from %I.dim_workspaces', :'marts_schema'),
    'Enrichment must not multiply or discard workspaces.'
);

SELECT pg_temp.add_equal_check(
    41, 'staging -> marts', 'dim_users row parity',
    format('select count(*)::numeric from %I.stg_users', :'staging_schema'),
    format('select count(*)::numeric from %I.dim_users', :'marts_schema'),
    'The inner workspace join must not discard users.'
);

SELECT pg_temp.add_equal_check(
    42, 'staging -> marts', 'dim_plans filtered row parity',
    format(
        $query$
        select count(*)::numeric
        from %I.stg_plans
        where not has_negative_price
          and not has_invalid_annual_price
        $query$,
        :'staging_schema'
    ),
    format('select count(*)::numeric from %I.dim_plans', :'marts_schema'),
    'The expected side repeats the documented dim_plans quality filter.'
);

SELECT pg_temp.add_equal_check(
    43, 'staging -> marts', 'fct_sessions row parity',
    format('select count(*)::numeric from %I.stg_sessions', :'staging_schema'),
    format('select count(*)::numeric from %I.fct_sessions', :'marts_schema'),
    'The inner user/workspace joins must not discard sessions.'
);

SELECT pg_temp.add_equal_check(
    44, 'staging -> marts', 'fct_events row parity',
    format('select count(*)::numeric from %I.stg_events', :'staging_schema'),
    format('select count(*)::numeric from %I.fct_events', :'marts_schema'),
    'Every staged event occurrence should remain in the fact.'
);

SELECT pg_temp.add_equal_check(
    45, 'staging -> marts', 'fct_subscriptions row parity',
    format('select count(*)::numeric from %I.stg_subscriptions', :'staging_schema'),
    format('select count(*)::numeric from %I.fct_subscriptions', :'marts_schema'),
    'The inner workspace join must not discard subscriptions.'
);

SELECT pg_temp.add_equal_check(
    46, 'staging -> marts', 'fct_subscription_plan_history row parity',
    format(
        'select count(*)::numeric from %I.stg_subscription_plan_history',
        :'staging_schema'
    ),
    format(
        'select count(*)::numeric from %I.fct_subscription_plan_history',
        :'marts_schema'
    ),
    'The inner subscription/workspace/plan joins must not discard history.'
);

SELECT pg_temp.add_equal_check(
    47, 'staging -> marts', 'fct_invoices row parity',
    format('select count(*)::numeric from %I.stg_invoices', :'staging_schema'),
    format('select count(*)::numeric from %I.fct_invoices', :'marts_schema'),
    'The inner workspace/plan joins must not discard invoices.'
);

SELECT pg_temp.add_equal_check(
    48, 'marts', 'invoice conversion row parity',
    format('select count(*)::numeric from %I.fct_invoices', :'marts_schema'),
    format(
        'select count(*)::numeric from %I.fct_invoices_converted',
        :'marts_schema'
    ),
    'The latest-prior FX lookup must still return exactly one row per invoice.'
);

SELECT pg_temp.add_zero_check(
    49,
    'marts',
    'dim_date is non-empty and continuous',
    format(
        $query$
        select case
            when count(*) > 0
             and count(*) = max(date_day) - min(date_day) + 1
            then 0::numeric
            else 1::numeric
        end
        from %I.dim_date
        $query$,
        :'marts_schema'
    ),
    'A continuous date dimension is required for DATEADD and TOTALYTD.'
);

SELECT pg_temp.add_key_set_check(
    50,
    'staging -> marts',
    'dim_workspaces key-set parity',
    format(
        'select workspace_key as record_key from %I.stg_workspaces',
        :'staging_schema'
    ),
    format(
        'select workspace_key as record_key from %I.dim_workspaces',
        :'marts_schema'
    ),
    'Checks business-row identity in addition to the row-count check.'
);

SELECT pg_temp.add_key_set_check(
    51,
    'staging -> marts',
    'dim_users key-set parity',
    format(
        'select user_key as record_key from %I.stg_users',
        :'staging_schema'
    ),
    format(
        'select user_key as record_key from %I.dim_users',
        :'marts_schema'
    ),
    'Detects a user discarded by the inner workspace join.'
);

SELECT pg_temp.add_key_set_check(
    52,
    'staging -> marts',
    'dim_plans filtered key-set parity',
    format(
        $query$
        select plan_key as record_key
        from %I.stg_plans
        where not has_negative_price
          and not has_invalid_annual_price
        $query$,
        :'staging_schema'
    ),
    format(
        'select plan_key as record_key from %I.dim_plans',
        :'marts_schema'
    ),
    'Expected keys repeat the documented dim_plans quality filter.'
);

SELECT pg_temp.add_key_set_check(
    53,
    'staging -> marts',
    'fct_sessions key-set parity',
    format(
        'select session_key as record_key from %I.stg_sessions',
        :'staging_schema'
    ),
    format(
        'select session_key as record_key from %I.fct_sessions',
        :'marts_schema'
    ),
    'Detects a session discarded by the inner user/workspace joins.'
);

SELECT pg_temp.add_key_set_check(
    54,
    'staging -> marts',
    'fct_events key-set parity',
    format(
        'select event_key as record_key from %I.stg_events',
        :'staging_schema'
    ),
    format(
        'select event_key as record_key from %I.fct_events',
        :'marts_schema'
    ),
    'Confirms every staged event occurrence remains traceable.'
);

SELECT pg_temp.add_key_set_check(
    55,
    'staging -> marts',
    'fct_subscriptions key-set parity',
    format(
        'select subscription_key as record_key from %I.stg_subscriptions',
        :'staging_schema'
    ),
    format(
        'select subscription_key as record_key from %I.fct_subscriptions',
        :'marts_schema'
    ),
    'Detects a subscription discarded by the inner workspace join.'
);

SELECT pg_temp.add_key_set_check(
    56,
    'staging -> marts',
    'fct_subscription_plan_history key-set parity',
    format(
        $query$
        select subscription_plan_period_key as record_key
        from %I.stg_subscription_plan_history
        $query$,
        :'staging_schema'
    ),
    format(
        $query$
        select subscription_plan_period_key as record_key
        from %I.fct_subscription_plan_history
        $query$,
        :'marts_schema'
    ),
    'Detects history discarded by subscription/workspace/plan joins.'
);

SELECT pg_temp.add_key_set_check(
    57,
    'staging -> marts',
    'fct_invoices key-set parity',
    format(
        'select invoice_key as record_key from %I.stg_invoices',
        :'staging_schema'
    ),
    format(
        'select invoice_key as record_key from %I.fct_invoices',
        :'marts_schema'
    ),
    'Detects an invoice discarded by workspace/plan joins.'
);

SELECT pg_temp.add_key_set_check(
    58,
    'marts',
    'invoice conversion key-set parity',
    format(
        'select invoice_key as record_key from %I.fct_invoices',
        :'marts_schema'
    ),
    format(
        'select invoice_key as record_key from %I.fct_invoices_converted',
        :'marts_schema'
    ),
    'Confirms one traceable converted result for every invoice key.'
);

-- ---------------------------------------------------------------------------
-- 4. Financial formulas, FX application, and aggregate reconciliation
-- ---------------------------------------------------------------------------

SELECT pg_temp.add_zero_check(
    59,
    'staging: invoice quality',
    'invoice quality flags match primitive fields',
    format(
        $query$
        select count(*)::numeric
        from %I.stg_invoices
        where amount_reconciliation_difference is distinct from
                (gross_amount - net_amount - tax_amount)::numeric(14, 2)
           or is_missing_currency is distinct from
                (source_currency_code is null)
           or has_negative_amount is distinct from
                coalesce(
                    net_amount < 0 or tax_amount < 0 or gross_amount < 0,
                    true
                )
           or has_amount_reconciliation_mismatch is distinct from
                coalesce(
                    abs(gross_amount - net_amount - tax_amount) > 0.01,
                    true
                )
           or has_invalid_billing_period is distinct from
                coalesce(period_end <= period_start, true)
           or has_invalid_due_date is distinct from
                coalesce(due_at < issued_at, true)
           or has_invalid_payment_lifecycle is distinct from
                coalesce(
                    (payment_status = 'paid' and paid_at is null)
                    or (payment_status <> 'paid' and paid_at is not null),
                    true
                )
        $query$,
        :'staging_schema'
    ),
    'Every stored quality flag is recomputed independently from source fields.'
);

SELECT pg_temp.add_zero_check(
    60,
    'marts: invoice eligibility',
    'eligibility formula matches primitive flags',
    format(
        $query$
        select count(*)::numeric
        from %I.fct_invoices
        where is_analytics_eligible is distinct from (
            payment_status = 'paid'
            and not is_missing_currency
            and not has_negative_amount
            and not has_amount_reconciliation_mismatch
            and not has_invalid_billing_period
            and not has_invalid_due_date
            and not has_invalid_payment_lifecycle
        )
        $query$,
        :'marts_schema'
    ),
    'This proves implementation consistency, not business approval of the rule.'
);

SELECT pg_temp.add_zero_check(
    61,
    'marts: invoice eligibility',
    'analytics source amounts obey eligibility',
    format(
        $query$
        select count(*)::numeric
        from %I.fct_invoices
        where (
            is_analytics_eligible
            and (
                analytics_net_amount is distinct from net_amount
                or analytics_tax_amount is distinct from tax_amount
                or analytics_gross_amount is distinct from gross_amount
            )
        )
        or (
            not is_analytics_eligible
            and (
                analytics_net_amount is not null
                or analytics_tax_amount is not null
                or analytics_gross_amount is not null
            )
        )
        $query$,
        :'marts_schema'
    ),
    'Ineligible rows must remain visible but contribute no analytics amount.'
);

SELECT pg_temp.add_zero_check(
    62,
    'FX',
    'all staged FX rates are positive USD quotes',
    format(
        $query$
        select count(*)::numeric
        from %I.stg_fx_rates
        where rate is null
           or rate <= 0
           or rate_date is null
           or base_currency is null
           or quote_currency is distinct from 'USD'
        $query$,
        :'staging_schema'
    ),
    'A non-positive rate or a different quote currency invalidates conversion.'
);

SELECT pg_temp.add_zero_check(
    63,
    'FX',
    'eligible non-USD invoices have FX coverage',
    format(
        $query$
        select count(*)::numeric
        from %I.fct_invoices_converted
        where is_analytics_eligible
          and source_currency_code <> 'USD'
          and fx_rate_to_usd is null
        $query$,
        :'marts_schema'
    ),
    'Revenue should not be certified unless this count is zero.'
);

SELECT pg_temp.add_zero_check(
    64,
    'FX',
    'applied FX date is the latest available date not after period_start',
    format(
        $query$
        select count(*)::numeric
        from %1$I.fct_invoices_converted as invoices
        where invoices.is_analytics_eligible
          and invoices.source_currency_code <> 'USD'
          and (
              invoices.fx_rate_date > invoices.period_start
              or invoices.fx_rate_date is distinct from (
                  select max(fx.rate_date)
                  from %2$I.stg_fx_rates as fx
                  where fx.base_currency = invoices.source_currency_code
                    and fx.quote_currency = 'USD'
                    and fx.rate_date <= invoices.period_start
              )
          )
        $query$,
        :'marts_schema',
        :'staging_schema'
    ),
    'This validates the implemented period_start/latest-prior convention.'
);

SELECT pg_temp.add_zero_check(
    65,
    'FX',
    'USD converted amounts equal independently recalculated amounts',
    format(
        $query$
        select count(*)::numeric
        from %I.fct_invoices_converted
        where is_analytics_eligible
          and (
              analytics_net_amount_usd is distinct from
                  case
                      when source_currency_code = 'USD'
                          then round(analytics_net_amount, 6)
                      when fx_rate_to_usd is not null
                          then round(analytics_net_amount * fx_rate_to_usd, 6)
                  end
              or analytics_tax_amount_usd is distinct from
                  case
                      when source_currency_code = 'USD'
                          then round(analytics_tax_amount, 6)
                      when fx_rate_to_usd is not null
                          then round(analytics_tax_amount * fx_rate_to_usd, 6)
                  end
              or analytics_gross_amount_usd is distinct from
                  case
                      when source_currency_code = 'USD'
                          then round(analytics_gross_amount, 6)
                      when fx_rate_to_usd is not null
                          then round(analytics_gross_amount * fx_rate_to_usd, 6)
                  end
          )
        $query$,
        :'marts_schema'
    ),
    'Expected values are recomputed from source amounts and the selected rate.'
);

SELECT pg_temp.add_zero_check(
    66,
    'marts: monthly billing',
    'monthly billing rows reconcile to invoice facts',
    format(
        $query$
        with expected as (
            select
                workspace_key,
                workspace_id,
                date_trunc('month', issued_at)::date as billing_month,
                source_currency_code,
                count(*) as invoice_count,
                count(*) filter (where payment_status = 'paid') as paid_invoice_count,
                count(*) filter (where is_analytics_eligible) as eligible_invoice_count,
                coalesce(sum(analytics_net_amount), 0)::numeric(18, 2)
                    as eligible_net_amount,
                coalesce(sum(analytics_tax_amount), 0)::numeric(18, 2)
                    as eligible_tax_amount,
                coalesce(sum(analytics_gross_amount), 0)::numeric(18, 2)
                    as eligible_gross_amount
            from %1$I.fct_invoices
            group by
                workspace_key,
                workspace_id,
                date_trunc('month', issued_at)::date,
                source_currency_code
        ),
        compared as (
            select
                expected.workspace_key as expected_workspace_key,
                actual.workspace_key as actual_workspace_key,
                expected.invoice_count as expected_invoice_count,
                actual.invoice_count as actual_invoice_count,
                expected.paid_invoice_count as expected_paid_invoice_count,
                actual.paid_invoice_count as actual_paid_invoice_count,
                expected.eligible_invoice_count as expected_eligible_invoice_count,
                actual.eligible_invoice_count as actual_eligible_invoice_count,
                expected.eligible_net_amount as expected_eligible_net_amount,
                actual.eligible_net_amount as actual_eligible_net_amount,
                expected.eligible_tax_amount as expected_eligible_tax_amount,
                actual.eligible_tax_amount as actual_eligible_tax_amount,
                expected.eligible_gross_amount as expected_eligible_gross_amount,
                actual.eligible_gross_amount as actual_eligible_gross_amount
            from expected
            full join %1$I.mart_workspace_monthly_billing as actual
                on actual.workspace_key = expected.workspace_key
               and actual.billing_month = expected.billing_month
               and actual.source_currency_code
                   is not distinct from expected.source_currency_code
        )
        select count(*)::numeric
        from compared
        where expected_workspace_key is null
           or actual_workspace_key is null
           or expected_invoice_count is distinct from actual_invoice_count
           or expected_paid_invoice_count is distinct from actual_paid_invoice_count
           or expected_eligible_invoice_count
               is distinct from actual_eligible_invoice_count
           or expected_eligible_net_amount is distinct from actual_eligible_net_amount
           or expected_eligible_tax_amount is distinct from actual_eligible_tax_amount
           or expected_eligible_gross_amount
               is distinct from actual_eligible_gross_amount
        $query$,
        :'marts_schema'
    ),
    'Every workspace-month-currency aggregate is rebuilt independently.'
);

\echo
\echo 'Automated gate results'
\echo '----------------------'
SELECT
    layer,
    check_name,
    expected_value,
    actual_value,
    status,
    details
FROM validation_results
ORDER BY check_order;

-- ---------------------------------------------------------------------------
-- 5. Independent SQL equivalents for the unfiltered Power BI KPI cards
-- ---------------------------------------------------------------------------

\echo
\echo 'Power BI reconciliation baseline (no report filters)'
\echo '----------------------------------------------------'
WITH invoice_metrics AS (
    SELECT
        count(distinct invoice_key)::numeric as invoices,
        count(distinct invoice_key)
            filter (where is_analytics_eligible)::numeric as eligible_invoices,
        count(distinct invoice_key)
            filter (where payment_status = 'paid')::numeric as paid_invoices,
        count(distinct invoice_key)
            filter (where payment_status = 'failed')::numeric as failed_invoices,
        sum(analytics_net_amount_usd)::numeric as net_revenue_usd,
        sum(analytics_tax_amount_usd)::numeric as tax_revenue_usd,
        sum(analytics_gross_amount_usd)::numeric as gross_revenue_usd,
        count(distinct invoice_key)
            filter (where is_missing_currency)::numeric
                as missing_invoice_currency_count,
        count(distinct invoice_key)
            filter (where has_amount_reconciliation_mismatch)::numeric
                as invoice_amount_mismatch_count,
        count(distinct invoice_key)
            filter (
                where is_analytics_eligible
                  and (
                      source_currency_code = 'USD'
                      or fx_rate_to_usd is not null
                  )
            )::numeric as fx_covered_eligible_invoices
    FROM :"marts_schema".fct_invoices_converted
),
user_metrics AS (
    SELECT
        count(distinct user_key)::numeric as users,
        count(distinct user_key)
            filter (where is_invalid_created_at)::numeric
                as invalid_user_created_at_count,
        count(distinct user_key)
            filter (where is_missing_country)::numeric
                as missing_user_country_count
    FROM :"marts_schema".dim_users
),
subscription_metrics AS (
    SELECT
        count(distinct subscription_key)::numeric as subscriptions,
        count(distinct subscription_key)
            filter (where subscription_status = 'active')::numeric
                as active_subscriptions,
        count(distinct subscription_key)
            filter (where subscription_status = 'cancelled')::numeric
                as cancelled_subscriptions,
        count(distinct workspace_key)::numeric as subscription_workspaces,
        count(distinct workspace_key)
            filter (where subscription_status = 'active')::numeric
                as active_subscription_workspaces
    FROM :"marts_schema".fct_subscriptions
),
metrics AS (
    SELECT 1 as metric_order, 'Invoices' as metric, invoices as expected_value
    FROM invoice_metrics
    UNION ALL
    SELECT 2, 'Eligible Invoices', eligible_invoices FROM invoice_metrics
    UNION ALL
    SELECT 3, 'Paid Invoices', paid_invoices FROM invoice_metrics
    UNION ALL
    SELECT 4, 'Failed Invoices', failed_invoices FROM invoice_metrics
    UNION ALL
    SELECT
        5,
        'Payment Success Rate',
        paid_invoices / nullif(invoices, 0)
    FROM invoice_metrics
    UNION ALL
    SELECT 6, 'Net Revenue USD', net_revenue_usd FROM invoice_metrics
    UNION ALL
    SELECT 7, 'Tax Revenue USD', tax_revenue_usd FROM invoice_metrics
    UNION ALL
    SELECT 8, 'Gross Revenue USD', gross_revenue_usd FROM invoice_metrics
    UNION ALL
    SELECT
        9,
        'Average Invoice Net USD',
        net_revenue_usd / nullif(eligible_invoices, 0)
    FROM invoice_metrics
    UNION ALL
    SELECT
        10,
        'Missing Invoice Currency Count',
        missing_invoice_currency_count
    FROM invoice_metrics
    UNION ALL
    SELECT
        11,
        'Invoice Amount Mismatch Count',
        invoice_amount_mismatch_count
    FROM invoice_metrics
    UNION ALL
    SELECT 12, 'Invalid User Created At Count', invalid_user_created_at_count
    FROM user_metrics
    UNION ALL
    SELECT 13, 'Missing User Country Count', missing_user_country_count
    FROM user_metrics
    UNION ALL
    SELECT
        14,
        'FX Covered Eligible Invoices',
        fx_covered_eligible_invoices
    FROM invoice_metrics
    UNION ALL
    SELECT
        15,
        'FX Coverage Rate',
        fx_covered_eligible_invoices / nullif(eligible_invoices, 0)
    FROM invoice_metrics
    UNION ALL
    SELECT 16, 'Subscriptions', subscriptions FROM subscription_metrics
    UNION ALL
    SELECT 17, 'Active Subscriptions', active_subscriptions
    FROM subscription_metrics
    UNION ALL
    SELECT 18, 'Canceled Subscriptions (contract value = cancelled)',
        cancelled_subscriptions
    FROM subscription_metrics
    UNION ALL
    SELECT 19, 'Paid Workspaces (current DAX definition)',
        subscription_workspaces
    FROM subscription_metrics
    UNION ALL
    SELECT 20, 'Active Paid Workspaces (current DAX definition)',
        active_subscription_workspaces
    FROM subscription_metrics
)
SELECT metric, round(expected_value, 6) as expected_value
FROM metrics
ORDER BY metric_order;

\echo
\echo 'Power BI monthly revenue baseline (active invoice issued-date path)'
\echo '------------------------------------------------------------------'
SELECT
    date_trunc('month', issued_at)::date as invoice_month,
    count(distinct invoice_key) as invoices,
    count(distinct invoice_key) filter (where is_analytics_eligible)
        as eligible_invoices,
    round(sum(analytics_net_amount_usd), 2) as net_revenue_usd
FROM :"marts_schema".fct_invoices_converted
GROUP BY date_trunc('month', issued_at)::date
ORDER BY invoice_month;

\echo
\echo 'Traceable invoice-quality examples (up to 25 rows)'
\echo '--------------------------------------------------'
SELECT
    invoice_id,
    workspace_id,
    subscription_id,
    plan_id,
    issued_at,
    period_start,
    source_currency_code,
    payment_status,
    net_amount,
    tax_amount,
    gross_amount,
    amount_reconciliation_difference,
    is_missing_currency,
    has_amount_reconciliation_mismatch,
    is_analytics_eligible,
    fx_rate_date,
    fx_rate_to_usd,
    analytics_net_amount_usd
FROM :"marts_schema".fct_invoices_converted
WHERE is_missing_currency
   OR has_amount_reconciliation_mismatch
ORDER BY issued_at, invoice_id
LIMIT 25;

SELECT
    CASE
        WHEN count(*) = 0 THEN 'true'
        ELSE 'false'
    END AS all_checks_passed
FROM validation_results
WHERE status = 'FAIL'
\gset

\echo
\if :all_checks_passed
  \echo 'FINAL RESULT: PASS - all automated SQL checks passed.'
\else
  \echo 'FINAL RESULT: FAIL - inspect rows marked FAIL above.'
  \quit 1
\endif
