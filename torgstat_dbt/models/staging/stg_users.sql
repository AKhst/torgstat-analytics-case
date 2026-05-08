with source as (
    select * from {{ source('raw_data', 'users') }}
),

renamed as (
    select
        user_id,
        -- Исправляем разные форматы дат (DD/MM/YYYY и YYYY-MM-DD)
        case 
            when signup_date ~ '^\d{2}/\d{2}/\d{4}$' 
                then to_date(signup_date, 'DD/MM/YYYY')
            else signup_date::date 
        end as signup_date,
        
        -- Обрабатываем грязные регионы
        coalesce(region, 'Unknown') as region_name
    from source
)

select * from renamed