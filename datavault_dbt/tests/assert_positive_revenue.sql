-- Fails if any corridor_stats row has negative total_revenue
SELECT *
FROM {{ ref('mart_corridor_stats') }}
WHERE total_revenue IS NOT NULL AND total_revenue < 0
