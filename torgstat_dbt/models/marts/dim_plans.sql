select
    plan_key,
    plan_id,
    plan_name,
    tier_rank,
    monthly_price,
    annual_price,
    is_active,
    tier_rank = 0 as is_free_plan,
    loaded_at_utc
from {{ ref('stg_plans') }}
where not has_negative_price
  and not has_invalid_annual_price
