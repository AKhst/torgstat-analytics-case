with source as (
    select
        user_id,
        workspace_id,
        signup_date,
        country,
        gdpr_consent,
        is_deleted,
        _source_file,
        _source_row_number,
        _load_batch_id,
        _loaded_at_utc
    from {{ source('raw_data', 'users') }}
),

typed as (
    select
        user_id::bigint as user_id,
        nullif(trim(workspace_id), '') as workspace_id,
        signup_date as signup_date_raw,
        {{ safe_iso_date('signup_date') }} as signup_date,
        case
            when country is null or trim(country) = '' then 'UNKNOWN'
            else upper(trim(country))
        end as country_code,
        coalesce(gdpr_consent::boolean, false) as has_gdpr_consent,
        coalesce(is_deleted::boolean, false) as is_deleted,
        _source_file as source_file_name,
        _source_row_number::bigint as source_row_number,
        _load_batch_id as load_batch_id,
        _loaded_at_utc as loaded_at_utc
    from source
)

select
    {{ generate_surrogate_key(['workspace_id', 'user_id']) }} as user_key,
    user_id,
    workspace_id,
    signup_date,
    country_code,
    has_gdpr_consent,
    is_deleted,
    signup_date_raw is null as is_missing_signup_date,
    signup_date_raw is not null and signup_date is null as is_invalid_signup_date,
    country_code = 'UNKNOWN' as is_missing_country,
    signup_date_raw,
    source_file_name,
    source_row_number,
    load_batch_id,
    loaded_at_utc
from typed
