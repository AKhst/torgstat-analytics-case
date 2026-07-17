with source as (
    select
        subscription_plan_period_id,
        subscription_id,
        plan_id,
        billing_frequency,
        valid_from,
        valid_to,
        change_type,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'subscription_plan_history') }}
)

select
    {{ generate_surrogate_key(['subscription_plan_period_id']) }} as subscription_plan_period_key,
    {{ generate_surrogate_key(['subscription_id']) }} as subscription_key,
    subscription_plan_period_id::bigint as subscription_plan_period_id,
    subscription_id::bigint as subscription_id,
    plan_id::integer as plan_id,
    lower(nullif(trim(billing_frequency), '')) as billing_frequency,
    valid_from::date as valid_from,
    valid_to::date as valid_to,
    lower(nullif(trim(change_type), '')) as change_type,
    coalesce(valid_to is not null and valid_to::date < valid_from::date, true)
        as has_invalid_period,
    _source_file as source_file_name,
    _source_row_number::bigint as source_row_number,
    _load_batch_id as load_batch_id,
    _loaded_at_utc as loaded_at_utc
from source
