with invoices as (
    select *
    from {{ ref('fct_invoices') }}
),

fx_candidates as (
    select
        invoices.invoice_key,
        fx.rate as fx_rate_to_usd,
        fx.rate_date,
        row_number() over (
            partition by invoices.invoice_key
            order by fx.rate_date desc
        ) as fx_rank
    from invoices
    left join {{ ref('stg_fx_rates') }} as fx
        on fx.base_currency = invoices.source_currency_code
       and fx.quote_currency = 'USD'
       and fx.rate_date <= invoices.period_start
)

select
    invoices.*,
    fx_candidates.fx_rate_to_usd,
    fx_candidates.rate_date as fx_rate_date,
    case
        when not invoices.is_analytics_eligible then null
        when invoices.source_currency_code = 'USD' then invoices.analytics_net_amount
        when fx_candidates.fx_rate_to_usd is not null
            then invoices.analytics_net_amount * fx_candidates.fx_rate_to_usd
    end::numeric(20, 6) as analytics_net_amount_usd,
    case
        when not invoices.is_analytics_eligible then null
        when invoices.source_currency_code = 'USD' then invoices.analytics_tax_amount
        when fx_candidates.fx_rate_to_usd is not null
            then invoices.analytics_tax_amount * fx_candidates.fx_rate_to_usd
    end::numeric(20, 6) as analytics_tax_amount_usd,
    case
        when not invoices.is_analytics_eligible then null
        when invoices.source_currency_code = 'USD' then invoices.analytics_gross_amount
        when fx_candidates.fx_rate_to_usd is not null
            then invoices.analytics_gross_amount * fx_candidates.fx_rate_to_usd
    end::numeric(20, 6) as analytics_gross_amount_usd
from invoices
left join fx_candidates
    on fx_candidates.invoice_key = invoices.invoice_key
   and fx_candidates.fx_rank = 1
