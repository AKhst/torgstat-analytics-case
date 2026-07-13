with source as (
    select
        workspace_id,
        event_date,
        event_name,
        properties,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'events') }}
),

typed as (
    select
        nullif(trim(workspace_id), '') as workspace_id,
        event_date::date as event_date,
        lower(nullif(trim(event_name), '')) as event_name,
        properties as event_properties_json,
        row_number() over (
            partition by workspace_id, event_date, event_name, properties
            order by _source_row_number
        ) as event_occurrence_number,
        count(*) over (
            partition by workspace_id, event_date, event_name, properties
        ) as event_record_count,
        _source_file as source_file_name,
        _source_row_number::bigint as source_row_number,
        _load_batch_id as load_batch_id,
        _loaded_at_utc as loaded_at_utc
    from source
)

select
    {{ generate_surrogate_key([
        'workspace_id',
        'event_date',
        'event_name',
        'event_properties_json',
        'event_occurrence_number'
    ]) }} as event_key,
    workspace_id,
    event_date,
    event_name,
    event_properties_json,
    event_occurrence_number,
    event_record_count,
    event_record_count > 1 as is_duplicate_event_payload,
    event_properties_json is null or trim(event_properties_json) = ''
        as is_missing_event_properties,
    source_file_name,
    source_row_number,
    load_batch_id,
    loaded_at_utc
from typed
