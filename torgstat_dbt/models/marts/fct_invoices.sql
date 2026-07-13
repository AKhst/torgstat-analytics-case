with enriched as (
    select
        invoice.invoice_key,
        invoice.subscription_key,
        {{ generate_surrogate_key(['invoice.workspace_id']) }} as workspace_key,
        plan.plan_key,
        invoice.invoice_id,
        invoice.subscription_id,
        invoice.workspace_id,
        invoice.plan_id,
        invoice.period_start,
        invoice.period_end,
        invoice.currency_code,
        invoice.net_amount,
        invoice.tax_amount,
        invoice.gross_amount,
        invoice.is_paid,
        invoice.is_missing_currency,
        invoice.is_negative_gross_amount,
        invoice.has_amount_mismatch,
        invoice.is_invalid_billing_period,
        invoice.is_reused_id_across_workspaces,
        not invoice.is_duplicate_invoice_key
            and invoice.is_paid
            and not invoice.is_missing_currency
            and not invoice.is_negative_gross_amount
            and not invoice.has_amount_mismatch
            and not invoice.is_invalid_billing_period
            as is_analytics_eligible,
        invoice.loaded_at_utc
    from {{ ref('stg_invoices') }} as invoice
    inner join {{ ref('stg_plans') }} as plan using (plan_id)
)

select
    *,
    case when is_analytics_eligible then gross_amount else null end
        as analytics_gross_amount
from enriched
