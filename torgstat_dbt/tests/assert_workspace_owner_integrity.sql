select
    workspaces.workspace_id,
    workspaces.is_active,
    count(users.user_id) as user_count,
    count(users.user_id) filter (where users.user_role = 'owner') as owner_count,
    count(users.user_id) filter (
        where users.user_role = 'owner' and users.is_active
    ) as active_owner_count
from {{ ref('stg_workspaces') }} as workspaces
left join {{ ref('stg_users') }} as users using (workspace_id)
group by workspaces.workspace_id, workspaces.is_active
having count(users.user_id) = 0
    or count(users.user_id) filter (where users.user_role = 'owner') != 1
    or (
        workspaces.is_active
        and count(users.user_id) filter (
            where users.user_role = 'owner' and users.is_active
        ) != 1
    )
