select
    user_key,
    {{ generate_surrogate_key(['workspace_id']) }} as workspace_key,
    user_id,
    workspace_id,
    signup_date,
    country_code,
    has_gdpr_consent,
    is_deleted,
    is_invalid_signup_date,
    is_missing_country,
    loaded_at_utc
from {{ ref('stg_users') }}
