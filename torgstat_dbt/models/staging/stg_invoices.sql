with source as (
    select
        invoice_id,
        subscription_id,
        workspace_id,
        plan_id,
        billing_frequency,
        issued_at,
        due_at,
        period_start,
        period_end,
        currency,
        net_amount,
        tax_amount,
        gross_amount,
        payment_status,
        paid_at,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'invoices') }}
),

typed as (
    select
        invoice_id::bigint as invoice_id,
        subscription_id::bigint as subscription_id,
        nullif(trim(workspace_id), '') as workspace_id,
        plan_id::integer as plan_id,
        lower(nullif(trim(billing_frequency), '')) as billing_frequency,
        issued_at::date as issued_at,
        due_at::date as due_at,
        period_start::date as period_start,
        period_end::date as period_end,
        upper(nullif(trim(currency), '')) as source_currency_code,
        net_amount::numeric(14, 2) as net_amount,
        tax_amount::numeric(14, 2) as tax_amount,
        gross_amount::numeric(14, 2) as gross_amount,
        lower(nullif(trim(payment_status), '')) as payment_status,
        paid_at::date as paid_at,
        _source_file as source_file_name,
        _source_row_number::bigint as source_row_number,
        _load_batch_id as load_batch_id,
        _loaded_at_utc as loaded_at_utc
    from source
)

select
    {{ generate_surrogate_key(['invoice_id']) }} as invoice_key,
    {{ generate_surrogate_key(['subscription_id']) }} as subscription_key,
    invoice_id,
    subscription_id,
    workspace_id,
    plan_id,
    billing_frequency,
    issued_at,
    due_at,
    period_start,
    period_end,
    source_currency_code,
    net_amount,
    tax_amount,
    gross_amount,
    payment_status,
    paid_at,
    (gross_amount - net_amount - tax_amount)::numeric(14, 2)
        as amount_reconciliation_difference,
    source_currency_code is null as is_missing_currency,
    coalesce(net_amount < 0 or tax_amount < 0 or gross_amount < 0, true)
        as has_negative_amount,
    coalesce(abs(gross_amount - net_amount - tax_amount) > 0.01, true)
        as has_amount_reconciliation_mismatch,
    coalesce(period_end <= period_start, true) as has_invalid_billing_period,
    coalesce(due_at < issued_at, true) as has_invalid_due_date,
    coalesce(
        (payment_status = 'paid' and paid_at is null)
            or (payment_status != 'paid' and paid_at is not null),
        true
    ) as has_invalid_payment_lifecycle,
    source_file_name,
    source_row_number,
    load_batch_id,
    loaded_at_utc
from typed
