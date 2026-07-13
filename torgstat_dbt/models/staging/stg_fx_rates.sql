with source as (
    select
        rate_date,
        base_currency,
        quote_currency,
        rate,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'fx_rates') }}
),
typed as (
    select
        rate_date::date as rate_date,
        upper(trim(base_currency)) as base_currency,
        upper(trim(quote_currency)) as quote_currency,
        rate::numeric(14, 6) as rate,
        _source_file as source_file_name,
        _source_row_number::bigint as source_row_number,
        _load_batch_id as load_batch_id,
        _loaded_at_utc as loaded_at_utc
    from source
)

select
    {{ generate_surrogate_key(['rate_date', 'base_currency', 'quote_currency']) }} as fx_rate_key,
    rate_date,
    base_currency,
    quote_currency,
    rate,
    source_file_name,
    source_row_number,
    load_batch_id,
    loaded_at_utc
from typed
