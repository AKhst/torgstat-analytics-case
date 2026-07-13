select
    session.session_key,
    users.user_key,
    {{ generate_surrogate_key(['users.workspace_id']) }} as workspace_key,
    session.session_id,
    session.user_id,
    users.workspace_id,
    session.session_date,
    session.utm_source,
    session.utm_medium,
    session.is_first_session,
    session.is_missing_utm_source,
    session.loaded_at_utc
from {{ ref('stg_sessions') }} as session
inner join {{ ref('stg_users') }} as users using (user_id)
