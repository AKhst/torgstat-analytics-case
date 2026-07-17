with ranked as (
    select
        session_id,
        user_id,
        started_at,
        is_first_session,
        row_number() over (
            partition by user_id
            order by started_at, session_id
        ) as session_rank,
        count(*) filter (where is_first_session) over (
            partition by user_id
        ) as first_session_count
    from {{ ref('stg_sessions') }}
)

select
    session_id,
    user_id,
    started_at,
    is_first_session,
    session_rank,
    first_session_count
from ranked
where first_session_count != 1
   or is_first_session != (session_rank = 1)
