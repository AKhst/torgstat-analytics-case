select
    invoices.invoice_id,
    invoices.plan_id
from {{ ref('stg_invoices') }} as invoices
inner join {{ ref('stg_plans') }} as plans using (plan_id)
where plans.tier_rank = 0
