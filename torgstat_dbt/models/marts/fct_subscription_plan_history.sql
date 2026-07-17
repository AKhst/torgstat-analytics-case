select
    history.subscription_plan_period_key,
    history.subscription_key,
    workspaces.workspace_key,
    plans.plan_key,
    history.subscription_plan_period_id,
    history.subscription_id,
    subscriptions.workspace_id,
    history.plan_id,
    history.billing_frequency,
    history.valid_from,
    history.valid_to,
    history.change_type,
    history.has_invalid_period,
    history.loaded_at_utc
from {{ ref('stg_subscription_plan_history') }} as history
inner join {{ ref('stg_subscriptions') }} as subscriptions using (subscription_id)
inner join {{ ref('stg_workspaces') }} as workspaces using (workspace_id)
inner join {{ ref('stg_plans') }} as plans using (plan_id)
