with source as (
    select * from {{ source('raw_data', 'invoices') }}
),

cleaned as (
    select
        invoice_id,
        subscription_id,
        plan_id,
        -- Обрабатываем невалидные суммы
        case 
            when amount = 'invalid_amount' then 0
            else coalesce(amount::numeric, 0)
        end as amount,
        
        -- Фильтруем или помечаем отрицательные суммы
        case when amount::numeric < 0 then true else false end as is_error_amount,
        
        discount_pct,
        paid as is_paid,
        
        -- Парсинг дат
        case 
            when period_start ~ '^\d{2}/\d{2}/\d{4}$' then to_date(period_start, 'DD/MM/YYYY')
            when period_start = 'invalid_date' then null
            else period_start::date 
        end as period_start_at,
        
        invoice_date::date as invoiced_at
    from source
)

select * from cleaned
where amount >= 0 -- Убираем финансовый мусор на уровне стейджинга