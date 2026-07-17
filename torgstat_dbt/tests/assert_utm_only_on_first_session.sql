select
    session_id,
    user_id,
    utm_source,
    utm_medium
from {{ ref('stg_sessions') }}
where has_utm_on_non_first_session
