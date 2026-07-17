with source as (
    select
        user_id,
        workspace_id,
        created_at,
        country_code,
        user_role,
        signup_type,
        has_gdpr_consent,
        is_active,
        deleted_at,
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
        created_at as created_at_raw,
        {{ safe_iso_timestamp('created_at') }} as created_at,
        upper(nullif(trim(country_code), '')) as country_code,
        lower(nullif(trim(user_role), '')) as user_role,
        lower(nullif(trim(signup_type), '')) as signup_type,
        coalesce(has_gdpr_consent::boolean, false) as has_gdpr_consent,
        coalesce(is_active::boolean, false) as is_active,
        {{ safe_iso_timestamp('deleted_at') }} as deleted_at,
        _source_file as source_file_name,
        _source_row_number::bigint as source_row_number,
        _load_batch_id as load_batch_id,
        _loaded_at_utc as loaded_at_utc
    from source
)

select
    {{ generate_surrogate_key(['user_id']) }} as user_key,
    user_id,
    workspace_id,
    created_at,
    country_code,
    user_role,
    signup_type,
    has_gdpr_consent,
    is_active,
    deleted_at,
    created_at_raw is null as is_missing_created_at,
    created_at_raw is not null and created_at is null as is_invalid_created_at,
    country_code is null as is_missing_country,
    is_active and deleted_at is not null as has_invalid_lifecycle,
    created_at_raw,
    source_file_name,
    source_row_number,
    load_batch_id,
    loaded_at_utc
from typed
