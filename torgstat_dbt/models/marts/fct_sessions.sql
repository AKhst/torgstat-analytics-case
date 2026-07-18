select
    sessions.session_key,
    users.user_key,
    workspaces.workspace_key,
    sessions.session_id,
    sessions.user_id,
    users.workspace_id,
    sessions.started_at,
    sessions.started_at::date as started_date,
    sessions.utm_source,
    sessions.utm_medium,
    sessions.is_first_session,
    sessions.is_missing_first_touch_source,
    sessions.has_utm_on_non_first_session,
    sessions.loaded_at_utc
from {{ ref('stg_sessions') }} as sessions
inner join {{ ref('stg_users') }} as users using (user_id)
inner join {{ ref('stg_workspaces') }} as workspaces using (workspace_id)
