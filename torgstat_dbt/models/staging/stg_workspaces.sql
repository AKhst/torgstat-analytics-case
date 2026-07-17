with source as (
    select
        workspace_id,
        workspace_name,
        created_at,
        country_code,
        customer_segment,
        billing_currency,
        is_active,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'workspaces') }}
)

select
    {{ generate_surrogate_key(['workspace_id']) }} as workspace_key,
    nullif(trim(workspace_id), '') as workspace_id,
    nullif(trim(workspace_name), '') as workspace_name,
    created_at::date as created_at,
    upper(nullif(trim(country_code), '')) as country_code,
    lower(nullif(trim(customer_segment), '')) as customer_segment,
    upper(nullif(trim(billing_currency), '')) as billing_currency,
    coalesce(is_active::boolean, false) as is_active,
    _source_file as source_file_name,
    _source_row_number::bigint as source_row_number,
    _load_batch_id as load_batch_id,
    _loaded_at_utc as loaded_at_utc
from source
