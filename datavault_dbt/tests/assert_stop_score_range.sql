-- Fails if any stop has performance_score outside 0-100
SELECT *
FROM {{ ref('mart_stop_performance') }}
WHERE performance_score < 0 OR performance_score > 100
