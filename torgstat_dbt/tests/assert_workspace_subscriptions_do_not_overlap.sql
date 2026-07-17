select
    left_subscription.workspace_id,
    left_subscription.subscription_id as left_subscription_id,
    right_subscription.subscription_id as right_subscription_id
from {{ ref('stg_subscriptions') }} as left_subscription
inner join {{ ref('stg_subscriptions') }} as right_subscription
    on left_subscription.workspace_id = right_subscription.workspace_id
   and left_subscription.subscription_id < right_subscription.subscription_id
   and left_subscription.started_at <= coalesce(right_subscription.ended_at, '9999-12-31'::date)
   and right_subscription.started_at <= coalesce(left_subscription.ended_at, '9999-12-31'::date)
