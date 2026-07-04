'''
macro safe_cast_numeric: É a função raiz. O núcleo é uma instrução CASE WHEN padrão do SQL. A linha com a sintaxe ~ '^[+-]?([0-9]+...' é uma validação direta via Regex. O sistema avalia se a string contém apenas caracteres que formam um número válido. Se a regra for atendida, ocorre a conversão matemática; caso o dado esteja corrompido com letras, a função injeta um valor nulo. Isso impede a falha crítica do banco de dados durante a compilação.
'''
{% macro safe_cast_numeric(expression) %}
    (
        case
            when nullif(trim(cast({{ expression }} as varchar)), '') is null then null
            when trim(cast({{ expression }} as varchar)) ~ '^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)$'
                then cast(trim(cast({{ expression }} as varchar)) as numeric)
            else null
        end
    )
{% endmacro %}

'''
macro safe_cast_numeric_column: Opera como uma camada de orquestração. A função recebe o nome da coluna e adiciona aspas duplas de segurança exigidas pelo PostgreSQL através do comando adapter.quote. Se houver a parametrização de que um caractere específico (como o traço -) representa ausência de dados, a macro insere um comando NULLIF para apagar esse ruído antes de enviar a coluna para a função raiz.
'''
{% macro safe_cast_numeric_column(column_name, null_value=none) %}
    {% set quoted_column = adapter.quote(column_name) %}
    {% if null_value is none %}
        {{ safe_cast_numeric(quoted_column) }}
    {% else %}
        {{ safe_cast_numeric("nullif(trim(" ~ quoted_column ~ "), '" ~ null_value ~ "')") }}
    {% endif %}
{% endmacro %}

'''
macro project_metric: Aplica a função regexp_replace para localizar e remover o padrão de texto .0 no final das strings, resolvendo falhas comuns de exportação de planilhas. O texto limpo é então repassado para a validação da função raiz.
'''
{% macro project_metric(column_name) %}
    {{ safe_cast_numeric("regexp_replace(" ~ adapter.quote(column_name) ~ ", '\.0$', '')") }}
{% endmacro %}
