select
    invoice_id,
    has_negative_amount,
    has_invalid_billing_period,
    has_invalid_due_date,
    has_invalid_payment_lifecycle
from {{ ref('stg_invoices') }}
where has_negative_amount
   or has_invalid_billing_period
   or has_invalid_due_date
   or has_invalid_payment_lifecycle
