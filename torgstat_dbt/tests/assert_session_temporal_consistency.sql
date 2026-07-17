select
    sessions.session_id,
    sessions.user_id,
    sessions.started_at,
    users.created_at
from {{ ref('stg_sessions') }} as sessions
inner join {{ ref('stg_users') }} as users using (user_id)
where users.created_at is not null
  and sessions.started_at < users.created_at
