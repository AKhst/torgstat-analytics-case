select
    subscriptions.subscription_key,
    workspaces.workspace_key,
    subscriptions.subscription_id,
    subscriptions.workspace_id,
    subscriptions.started_at,
    subscriptions.ended_at,
    subscriptions.subscription_status,
    subscriptions.has_invalid_period,
    subscriptions.has_invalid_lifecycle,
    subscriptions.loaded_at_utc
from {{ ref('stg_subscriptions') }} as subscriptions
inner join {{ ref('stg_workspaces') }} as workspaces using (workspace_id)
