select
    invoice_id,
    subscription_id,
    workspace_id,
    plan_id
from {{ ref('stg_invoices') }} as invoice
where not exists (
    select 1
    from {{ ref('stg_subscriptions') }} as subscription
    where subscription.subscription_id = invoice.subscription_id
      and subscription.workspace_id = invoice.workspace_id
      and subscription.plan_id = invoice.plan_id
)
