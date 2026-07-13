select
    {{ generate_surrogate_key([
        'workspace_key',
        "date_trunc('month', period_start)::date",
        'currency_code'
    ]) }} as workspace_month_currency_key,
    workspace_key,
    workspace_id,
    date_trunc('month', period_start)::date as billing_month,
    currency_code,
    count(*) as invoice_count,
    count(*) filter (where is_paid) as paid_invoice_count,
    count(*) filter (where is_analytics_eligible) as eligible_invoice_count,
    coalesce(sum(net_amount) filter (where is_analytics_eligible), 0)::numeric(18, 2)
        as eligible_net_amount,
    coalesce(sum(tax_amount) filter (where is_analytics_eligible), 0)::numeric(18, 2)
        as eligible_tax_amount,
    coalesce(sum(gross_amount) filter (where is_analytics_eligible), 0)::numeric(18, 2)
        as eligible_gross_amount,
    max(loaded_at_utc) as loaded_at_utc
from {{ ref('fct_invoices') }}
group by
    workspace_key,
    workspace_id,
    date_trunc('month', period_start)::date,
    currency_code
