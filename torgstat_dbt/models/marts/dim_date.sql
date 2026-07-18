with date_values as (
    select created_at as date_day
    from {{ ref('dim_workspaces') }}

    union

    select created_at::date as date_day
    from {{ ref('dim_users') }}
    where created_at is not null

    union

    select started_date as date_day
    from {{ ref('fct_sessions') }}

    union

    select event_date as date_day
    from {{ ref('fct_events') }}

    union

    select started_at as date_day
    from {{ ref('fct_subscriptions') }}

    union

    select ended_at as date_day
    from {{ ref('fct_subscriptions') }}
    where ended_at is not null

    union

    select issued_at as date_day
    from {{ ref('fct_invoices') }}

    union

    select due_at as date_day
    from {{ ref('fct_invoices') }}

    union

    select paid_at as date_day
    from {{ ref('fct_invoices') }}
    where paid_at is not null

    union

    select period_start as date_day
    from {{ ref('fct_invoices') }}

    union

    select period_end as date_day
    from {{ ref('fct_invoices') }}
),

date_bounds as (
    select
        date_trunc('year', min(date_day))::date as min_date,
        (date_trunc('year', max(date_day)) + interval '1 year' - interval '1 day')::date as max_date
    from date_values
),

date_spine as (
    select generated_date::date as date_day
    from date_bounds
    cross join generate_series(min_date, max_date, interval '1 day') as generated_date
)

select
    date_day,
    extract(year from date_day)::integer as calendar_year,
    extract(quarter from date_day)::integer as calendar_quarter,
    extract(month from date_day)::integer as month_number,
    to_char(date_day, 'Mon') as month_name_short,
    to_char(date_day, 'Month') as month_name,
    date_trunc('month', date_day)::date as month_start_date,
    (date_trunc('month', date_day) + interval '1 month' - interval '1 day')::date as month_end_date,
    to_char(date_day, 'YYYY-MM') as year_month,
    extract(week from date_day)::integer as iso_week_number,
    extract(isodow from date_day)::integer as iso_day_of_week,
    to_char(date_day, 'Dy') as day_name_short,
    to_char(date_day, 'Day') as day_name,
    (extract(isodow from date_day) in (6, 7)) as is_weekend
from date_spine
