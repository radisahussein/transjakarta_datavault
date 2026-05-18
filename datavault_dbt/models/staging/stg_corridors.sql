SELECT
    corridor_id,
    corridor_name
FROM {{ ref('corridors') }}
WHERE corridor_id IS NOT NULL
