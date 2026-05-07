with source as (
    
    -- Функция source говорит dbt: "Возьми таблицу users из источника torgstat"
    select * from {{ source('torgstat', 'users') }}

),

renamed as (

    select
        user_id,
        signup_date,
        region
        -- Тут можно добавить другие колонки, если они есть
    from source

)

select * from renamed