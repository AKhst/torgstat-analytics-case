with user_metrics as (
    select
        workspace_id,
        count(*) as user_count,
        count(*) filter (where is_active) as active_user_count,
        count(*) filter (where user_role = 'owner') as owner_count,
        count(*) filter (where user_role = 'owner' and is_active) as active_owner_count
    from {{ ref('stg_users') }}
    group by workspace_id
),

subscription_metrics as (
    select
        workspace_id,
        count(*) as subscription_count,
        count(*) filter (where subscription_status in ('active', 'past_due', 'trial'))
            as active_subscription_count
    from {{ ref('stg_subscriptions') }}
    group by workspace_id
),

owner_sessions as (
    select
        users.workspace_id,
        sessions.utm_source,
        sessions.utm_medium,
        row_number() over (
            partition by users.workspace_id
            order by sessions.started_at, sessions.session_id
        ) as session_rank
    from {{ ref('stg_users') }} as users
    inner join {{ ref('stg_sessions') }} as sessions using (user_id)
    where users.user_role = 'owner'
      and sessions.is_first_session
)

select
    workspaces.workspace_key,
    workspaces.workspace_id,
    workspaces.workspace_name,
    workspaces.created_at,
    workspaces.country_code,
    workspaces.customer_segment,
    workspaces.billing_currency,
    workspaces.is_active,
    coalesce(user_metrics.user_count, 0)::bigint as user_count,
    coalesce(user_metrics.active_user_count, 0)::bigint as active_user_count,
    coalesce(user_metrics.owner_count, 0)::bigint as owner_count,
    coalesce(user_metrics.active_owner_count, 0)::bigint as active_owner_count,
    coalesce(subscription_metrics.subscription_count, 0)::bigint as subscription_count,
    coalesce(subscription_metrics.active_subscription_count, 0)::bigint
        as active_subscription_count,
    owner_sessions.utm_source as acquisition_source,
    owner_sessions.utm_medium as acquisition_medium,
    workspaces.loaded_at_utc
from {{ ref('stg_workspaces') }} as workspaces
left join user_metrics using (workspace_id)
left join subscription_metrics using (workspace_id)
left join owner_sessions
    on owner_sessions.workspace_id = workspaces.workspace_id
   and owner_sessions.session_rank = 1
