select
    country_code,
    country_name_en
from {{ ref('country_reference') }}
