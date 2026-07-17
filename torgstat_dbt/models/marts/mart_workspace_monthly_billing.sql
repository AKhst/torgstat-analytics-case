select
    {{ generate_surrogate_key([
        'workspace_key',
        "date_trunc('month', issued_at)::date",
        'source_currency_code'
    ]) }} as workspace_month_currency_key,
    workspace_key,
    workspace_id,
    date_trunc('month', issued_at)::date as billing_month,
    source_currency_code,
    count(*) as invoice_count,
    count(*) filter (where payment_status = 'paid') as paid_invoice_count,
    count(*) filter (where is_analytics_eligible) as eligible_invoice_count,
    coalesce(sum(analytics_net_amount), 0)::numeric(18, 2) as eligible_net_amount,
    coalesce(sum(analytics_tax_amount), 0)::numeric(18, 2) as eligible_tax_amount,
    coalesce(sum(analytics_gross_amount), 0)::numeric(18, 2) as eligible_gross_amount,
    max(loaded_at_utc) as loaded_at_utc
from {{ ref('fct_invoices') }}
group by
    workspace_key,
    workspace_id,
    date_trunc('month', issued_at)::date,
    source_currency_code
