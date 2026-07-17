with source as (
    select
        plan_id,
        plan_name,
        tier_rank,
        monthly_price,
        annual_price,
        is_active,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'plans') }}
)

select
    {{ generate_surrogate_key(['plan_id']) }} as plan_key,
    plan_id::integer as plan_id,
    nullif(trim(plan_name), '') as plan_name,
    tier_rank::integer as tier_rank,
    monthly_price::numeric(14, 2) as monthly_price,
    annual_price::numeric(14, 2) as annual_price,
    coalesce(is_active::boolean, false) as is_active,
    coalesce(monthly_price < 0 or annual_price < 0, false) as has_negative_price,
    coalesce(monthly_price > 0 and annual_price != monthly_price * 10, true)
        as has_invalid_annual_price,
    _source_file as source_file_name,
    _source_row_number::bigint as source_row_number,
    _load_batch_id as load_batch_id,
    _loaded_at_utc as loaded_at_utc
from source
