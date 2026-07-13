with invoices as (
    select
        invoice_key,
        invoice_id,
        subscription_id,
        workspace_id,
        plan_id,
        period_start,
        period_end,
        currency_code,
        net_amount,
        tax_amount,
        gross_amount,
        is_paid,
        is_missing_currency,
        is_negative_gross_amount,
        has_amount_mismatch,
        is_invalid_billing_period,
        is_reused_id_across_workspaces,
        not is_duplicate_invoice_key
            and is_paid
            and not is_missing_currency
            and not is_negative_gross_amount
            and not has_amount_mismatch
            and not is_invalid_billing_period
            as is_analytics_eligible,
        loaded_at_utc
    from {{ ref('stg_invoices') }}
),
fx as (
    select
        rate_date,
        base_currency,
        quote_currency,
        rate
    from {{ ref('stg_fx_rates') }}
),
fx_with_fallback as (
    select
        invoices.invoice_key,
        invoices.period_start,
        invoices.currency_code,
        fx.rate as fx_rate_to_usd,
        fx.rate_date,
        row_number() over (
            partition by invoices.invoice_key
            order by abs((fx.rate_date::date - invoices.period_start::date)) asc, fx.rate_date desc
        ) as fx_rank
    from invoices
    left join fx
        on fx.base_currency = invoices.currency_code
       and fx.quote_currency = 'USD'
       and fx.rate_date <= invoices.period_start::date
)

select
    invoices.invoice_key,
    invoices.invoice_id,
    invoices.subscription_id,
    invoices.workspace_id,
    invoices.plan_id,
    invoices.period_start,
    invoices.period_end,
    invoices.currency_code,
    invoices.net_amount,
    invoices.tax_amount,
    invoices.gross_amount,
    invoices.is_paid,
    invoices.is_missing_currency,
    invoices.is_negative_gross_amount,
    invoices.has_amount_mismatch,
    invoices.is_invalid_billing_period,
    invoices.is_analytics_eligible,
    fx_with_fallback.fx_rate_to_usd,
    case
        when invoices.currency_code = 'USD' then invoices.gross_amount
        when fx_with_fallback.fx_rate_to_usd is not null then invoices.gross_amount * fx_with_fallback.fx_rate_to_usd
        else null
    end as gross_amount_usd,
    case
        when invoices.currency_code = 'USD' then invoices.net_amount
        when fx_with_fallback.fx_rate_to_usd is not null then invoices.net_amount * fx_with_fallback.fx_rate_to_usd
        else null
    end as net_amount_usd,
    case
        when invoices.currency_code = 'USD' then invoices.tax_amount
        when fx_with_fallback.fx_rate_to_usd is not null then invoices.tax_amount * fx_with_fallback.fx_rate_to_usd
        else null
    end as tax_amount_usd,
    invoices.loaded_at_utc
from invoices
left join fx_with_fallback
    on fx_with_fallback.invoice_key = invoices.invoice_key
   and fx_with_fallback.fx_rank = 1
