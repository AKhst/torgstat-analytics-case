{% macro safe_iso_timestamp(expression) -%}
    case
        when {{ expression }} ~ '^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]) ([01]\d|2[0-3]):[0-5]\d:[0-5]\d$'
            and to_char(to_timestamp({{ expression }}, 'YYYY-MM-DD HH24:MI:SS'), 'YYYY-MM-DD HH24:MI:SS') = {{ expression }}
            then to_timestamp({{ expression }}, 'YYYY-MM-DD HH24:MI:SS')::timestamp
        else null
    end
{%- endmacro %}
