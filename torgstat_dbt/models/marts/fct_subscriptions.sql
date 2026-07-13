select
    subscription.subscription_key,
    {{ generate_surrogate_key(['subscription.workspace_id']) }} as workspace_key,
    plan.plan_key,
    subscription.subscription_id,
    subscription.workspace_id,
    subscription.plan_id,
    subscription.start_date,
    subscription.subscription_status,
    subscription.is_missing_subscription_status,
    subscription.is_reused_id_across_workspaces,
    subscription.loaded_at_utc
from {{ ref('stg_subscriptions') }} as subscription
inner join {{ ref('stg_plans') }} as plan using (plan_id)
where not subscription.is_duplicate_subscription_key
