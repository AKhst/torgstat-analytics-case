with source as (
    select
        subscription_id,
        workspace_id,
        started_at,
        ended_at,
        status,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'subscriptions') }}
)

select
    {{ generate_surrogate_key(['subscription_id']) }} as subscription_key,
    subscription_id::bigint as subscription_id,
    nullif(trim(workspace_id), '') as workspace_id,
    started_at::date as started_at,
    ended_at::date as ended_at,
    lower(nullif(trim(status), '')) as subscription_status,
    coalesce(ended_at is not null and ended_at::date < started_at::date, true)
        as has_invalid_period,
    coalesce(
        lower(nullif(trim(status), '')) = 'cancelled' and ended_at is null,
        true
    ) as has_invalid_lifecycle,
    _source_file as source_file_name,
    _source_row_number::bigint as source_row_number,
    _load_batch_id as load_batch_id,
    _loaded_at_utc as loaded_at_utc
from source
