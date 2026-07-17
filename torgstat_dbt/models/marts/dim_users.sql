select
    users.user_key,
    workspaces.workspace_key,
    users.user_id,
    users.workspace_id,
    users.created_at,
    users.country_code,
    users.user_role,
    users.signup_type,
    users.has_gdpr_consent,
    users.is_active,
    users.deleted_at,
    users.is_invalid_created_at,
    users.is_missing_country,
    users.has_invalid_lifecycle,
    users.loaded_at_utc
from {{ ref('stg_users') }} as users
inner join {{ ref('stg_workspaces') }} as workspaces using (workspace_id)
