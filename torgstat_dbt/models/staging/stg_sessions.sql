with source as (
    select
        session_id,
        user_id,
        session_date,
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
    session_date::date as session_date,
    lower(nullif(trim(utm_source), '')) as utm_source,
    lower(nullif(trim(utm_medium), '')) as utm_medium,
    coalesce(is_first_session::boolean, false) as is_first_session,
    utm_source is null or trim(utm_source) = '' as is_missing_utm_source,
    _source_file as source_file_name,
    _source_row_number::bigint as source_row_number,
    _load_batch_id as load_batch_id,
    _loaded_at_utc as loaded_at_utc
from source
