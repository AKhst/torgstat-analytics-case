with source as (
    select
        plan_id,
        plan_name,
        billing_period,
        price,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'plans') }}
)

select
    {{ generate_surrogate_key(['plan_id']) }} as plan_key,
    plan_id::integer as plan_id,
    trim(plan_name) as plan_name,
    lower(trim(billing_period)) as billing_period,
    price::numeric(14, 2) as price,
    coalesce(price < 0, false) as is_negative_price,
    coalesce(lower(trim(billing_period)) not in ('monthly', 'annual'), true)
        as is_invalid_billing_period,
    _source_file as source_file_name,
    _source_row_number::bigint as source_row_number,
    _load_batch_id as load_batch_id,
    _loaded_at_utc as loaded_at_utc
from source
