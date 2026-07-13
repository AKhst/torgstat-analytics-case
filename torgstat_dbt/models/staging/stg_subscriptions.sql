with source as (
    select
        subscription_id,
        workspace_id,
        plan_id,
        start_date,
        status,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'subscriptions') }}
),

typed as (
    select
        subscription_id::bigint as subscription_id,
        nullif(trim(workspace_id), '') as workspace_id,
        plan_id::integer as plan_id,
        start_date::date as start_date,
        case
            when status is null or trim(status) in ('', 'MISSING_STATUS') then 'unknown'
            else lower(trim(status))
        end as subscription_status,
        status as subscription_status_raw,
        count(*) over (partition by workspace_id, subscription_id)
            as subscription_key_record_count,
        count(*) over (partition by subscription_id) as subscription_id_record_count,
        _source_file as source_file_name,
        _source_row_number::bigint as source_row_number,
        _load_batch_id as load_batch_id,
        _loaded_at_utc as loaded_at_utc
    from source
)

select
    {{ generate_surrogate_key(['workspace_id', 'subscription_id']) }} as subscription_key,
    subscription_id,
    workspace_id,
    plan_id,
    start_date,
    subscription_status,
    subscription_key_record_count,
    subscription_id_record_count,
    subscription_key_record_count > 1 as is_duplicate_subscription_key,
    subscription_id_record_count > 1 as is_reused_id_across_workspaces,
    subscription_status = 'unknown' as is_missing_subscription_status,
    subscription_status_raw,
    source_file_name,
    source_row_number,
    load_batch_id,
    loaded_at_utc
from typed
