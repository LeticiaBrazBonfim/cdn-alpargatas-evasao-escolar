WITH RECURSIVE gerador_anos AS (
    SELECT 2000 AS ano
    
    UNION ALL
    
    SELECT ano + 1
    FROM gerador_anos
    WHERE ano < 2031
)

SELECT 
    MD5(CAST(ano AS VARCHAR)) AS sk_calendario,
    ano AS ano_referencia
FROM gerador_anos
ORDER BY ano