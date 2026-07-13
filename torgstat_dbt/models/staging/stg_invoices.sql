with source as (
    select
        invoice_id,
        subscription_id,
        workspace_id,
        plan_id,
        period_start,
        period_end,
        currency,
        net_amount,
        tax_amount,
        gross_amount,
        paid,
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
        period_start::date as period_start,
        period_end::date as period_end,
        case
            when currency is null or trim(currency) = '' then 'UNKNOWN'
            else upper(trim(currency))
        end as currency_code,
        net_amount::numeric(14, 2) as net_amount,
        tax_amount::numeric(14, 2) as tax_amount,
        gross_amount::numeric(14, 2) as gross_amount,
        coalesce(paid::boolean, false) as is_paid,
        count(*) over (partition by workspace_id, invoice_id) as invoice_key_record_count,
        count(*) over (partition by invoice_id) as invoice_id_record_count,
        _source_file as source_file_name,
        _source_row_number::bigint as source_row_number,
        _load_batch_id as load_batch_id,
        _loaded_at_utc as loaded_at_utc
    from source
)

select
    {{ generate_surrogate_key(['workspace_id', 'invoice_id']) }} as invoice_key,
    {{ generate_surrogate_key(['workspace_id', 'subscription_id']) }} as subscription_key,
    invoice_id,
    subscription_id,
    workspace_id,
    plan_id,
    period_start,
    period_end,
    currency_code,
    net_amount,
    tax_amount,
    gross_amount,
    is_paid,
    invoice_key_record_count,
    invoice_id_record_count,
    invoice_key_record_count > 1 as is_duplicate_invoice_key,
    invoice_id_record_count > 1 as is_reused_id_across_workspaces,
    currency_code = 'UNKNOWN' as is_missing_currency,
    gross_amount < 0 as is_negative_gross_amount,
    abs(gross_amount - (net_amount + tax_amount)) > 0.01 as has_amount_mismatch,
    period_end <= period_start as is_invalid_billing_period,
    source_file_name,
    source_row_number,
    load_batch_id,
    loaded_at_utc
from typed
