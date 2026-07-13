select
    plan_key,
    plan_id,
    plan_name,
    billing_period,
    price,
    price = 0 as is_free_plan,
    loaded_at_utc
from {{ ref('stg_plans') }}
where not is_negative_price
  and not is_invalid_billing_period
