SELECT
    stop_id,
    stop_name,
    lat,
    lon
FROM {{ ref('stops') }}
WHERE stop_id IS NOT NULL
