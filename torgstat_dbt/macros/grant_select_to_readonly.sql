{% macro grant_select_to_readonly() -%}
    grant select on {{ this }} to {{ adapter.quote(env_var('READONLY_USER', 'readonly')) }}
{%- endmacro %}
