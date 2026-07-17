with source as (
    select
        session_id,
        user_id,
        started_at,
        utm_source,
        utm_medium,
        is_first_session,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'sessions') }}
)

select
    {{ generate_surrogate_key(['session_id']) }} as session_key,
    nullif(trim(session_id), '') as session_id,
    user_id::bigint as user_id,
    started_at::timestamp as started_at,
    lower(nullif(trim(utm_source), '')) as utm_source,
    lower(nullif(trim(utm_medium), '')) as utm_medium,
    coalesce(is_first_session::boolean, false) as is_first_session,
    coalesce(is_first_session::boolean, false) and utm_source is null
        as is_missing_first_touch_source,
    not coalesce(is_first_session::boolean, false)
        and (utm_source is not null or utm_medium is not null)
        as has_utm_on_non_first_session,
    _source_file as source_file_name,
    _source_row_number::bigint as source_row_number,
    _load_batch_id as load_batch_id,
    _loaded_at_utc as loaded_at_utc
from source
