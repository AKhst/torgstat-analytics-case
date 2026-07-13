{% macro safe_iso_date(expression) -%}
    case
        when {{ expression }} ~ '^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$' then
            case
                when to_char(to_date({{ expression }}, 'YYYY-MM-DD'), 'YYYY-MM-DD') = {{ expression }}
                    then to_date({{ expression }}, 'YYYY-MM-DD')
                else null
            end
        else null
    end
{%- endmacro %}
