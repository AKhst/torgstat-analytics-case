select
    invoices.invoice_id,
    invoices.subscription_id,
    invoices.workspace_id,
    invoices.plan_id,
    invoices.billing_frequency,
    invoices.period_start
from {{ ref('stg_invoices') }} as invoices
where not exists (
    select 1
    from {{ ref('stg_subscriptions') }} as subscriptions
    where subscriptions.subscription_id = invoices.subscription_id
      and subscriptions.workspace_id = invoices.workspace_id
)
or not exists (
    select 1
    from {{ ref('stg_subscription_plan_history') }} as history
    where history.subscription_id = invoices.subscription_id
      and history.plan_id = invoices.plan_id
      and history.billing_frequency = invoices.billing_frequency
      and invoices.period_start >= history.valid_from
      and (history.valid_to is null or invoices.period_start <= history.valid_to)
)
