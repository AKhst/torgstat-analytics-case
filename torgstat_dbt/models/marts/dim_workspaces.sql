with workspace_spine as (
    select workspace_id, loaded_at_utc from {{ ref('stg_users') }}
    union all
    select workspace_id, loaded_at_utc from {{ ref('stg_subscriptions') }}
    union all
    select workspace_id, loaded_at_utc from {{ ref('stg_invoices') }}
    union all
    select workspace_id, loaded_at_utc from {{ ref('stg_events') }}
),

workspaces as (
    select
        workspace_id,
        max(loaded_at_utc) as loaded_at_utc
    from workspace_spine
    group by workspace_id
),

user_metrics as (
    select
        workspace_id,
        min(signup_date) as first_user_signup_date,
        count(*) as user_count,
        count(*) filter (where not is_deleted) as active_user_count,
        count(distinct nullif(country_code, 'UNKNOWN')) as country_count
    from {{ ref('stg_users') }}
    group by workspace_id
),

subscription_metrics as (
    select
        workspace_id,
        min(start_date) as first_subscription_date,
        count(*) as subscription_count,
        count(*) filter (where subscription_status = 'active') as active_subscription_count
    from {{ ref('stg_subscriptions') }}
    group by workspace_id
)

select
    {{ generate_surrogate_key(['workspaces.workspace_id']) }} as workspace_key,
    workspaces.workspace_id,
    user_metrics.first_user_signup_date,
    coalesce(user_metrics.user_count, 0)::bigint as user_count,
    coalesce(user_metrics.active_user_count, 0)::bigint as active_user_count,
    coalesce(user_metrics.country_count, 0)::bigint as country_count,
    subscription_metrics.first_subscription_date,
    coalesce(subscription_metrics.subscription_count, 0)::bigint as subscription_count,
    coalesce(subscription_metrics.active_subscription_count, 0)::bigint
        as active_subscription_count,
    workspaces.loaded_at_utc
from workspaces
left join user_metrics using (workspace_id)
left join subscription_metrics using (workspace_id)
