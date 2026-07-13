select
    event_key,
    {{ generate_surrogate_key(['workspace_id']) }} as workspace_key,
    workspace_id,
    event_date,
    event_name,
    event_properties_json,
    event_occurrence_number,
    is_duplicate_event_payload,
    loaded_at_utc
from {{ ref('stg_events') }}
