with enriched as (
    select
        invoices.invoice_key,
        invoices.subscription_key,
        workspaces.workspace_key,
        plans.plan_key,
        invoices.invoice_id,
        invoices.subscription_id,
        invoices.workspace_id,
        invoices.plan_id,
        invoices.billing_frequency,
        invoices.issued_at,
        invoices.due_at,
        invoices.period_start,
        invoices.period_end,
        invoices.source_currency_code,
        invoices.net_amount,
        invoices.tax_amount,
        invoices.gross_amount,
        invoices.payment_status,
        invoices.paid_at,
        invoices.amount_reconciliation_difference,
        invoices.is_missing_currency,
        invoices.has_negative_amount,
        invoices.has_amount_reconciliation_mismatch,
        invoices.has_invalid_billing_period,
        invoices.has_invalid_due_date,
        invoices.has_invalid_payment_lifecycle,
        invoices.payment_status = 'paid'
            and not invoices.is_missing_currency
            and not invoices.has_negative_amount
            and not invoices.has_amount_reconciliation_mismatch
            and not invoices.has_invalid_billing_period
            and not invoices.has_invalid_due_date
            and not invoices.has_invalid_payment_lifecycle
            as is_analytics_eligible,
        invoices.loaded_at_utc
    from {{ ref('stg_invoices') }} as invoices
    inner join {{ ref('stg_workspaces') }} as workspaces using (workspace_id)
    inner join {{ ref('stg_plans') }} as plans using (plan_id)
)

select
    *,
    case when is_analytics_eligible then net_amount end as analytics_net_amount,
    case when is_analytics_eligible then tax_amount end as analytics_tax_amount,
    case when is_analytics_eligible then gross_amount end as analytics_gross_amount
from enriched
