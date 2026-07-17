select
    left_period.subscription_plan_period_id as left_period_id,
    right_period.subscription_plan_period_id as right_period_id,
    left_period.subscription_id,
    left_period.valid_from as left_valid_from,
    left_period.valid_to as left_valid_to,
    right_period.valid_from as right_valid_from,
    right_period.valid_to as right_valid_to
from {{ ref('stg_subscription_plan_history') }} as left_period
inner join {{ ref('stg_subscription_plan_history') }} as right_period
    on left_period.subscription_id = right_period.subscription_id
   and left_period.subscription_plan_period_id < right_period.subscription_plan_period_id
   and left_period.valid_from <= coalesce(right_period.valid_to, '9999-12-31'::date)
   and right_period.valid_from <= coalesce(left_period.valid_to, '9999-12-31'::date)
