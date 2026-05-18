WITH trips AS (
    SELECT * FROM {{ ref('stg_transactions') }}
),

stops AS (
    SELECT stop_id, lat, lon FROM {{ ref('stg_stops') }}
),

joined AS (
    SELECT
        t.*,
        s.lat AS tap_in_stop_lat,
        s.lon AS tap_in_stop_lon
    FROM trips t
    LEFT JOIN stops s ON t.tap_in_stop_id = s.stop_id
),

enriched AS (
    SELECT
        transaction_id,
        card_id,
        card_bank,
        card_sex,
        birth_year,
        age_years,
        corridor_id,
        corridor_name,
        direction,
        tap_in_stop_id,
        tap_in_stop_name,
        tap_in_lat,
        tap_in_lon,
        tap_in_seq,
        tap_in_time,
        tap_out_stop_id,
        tap_out_stop_name,
        tap_out_lat,
        tap_out_lon,
        tap_out_seq,
        tap_out_time,
        pay_amount,
        has_tap_out,

        -- temporal features
        CAST(tap_in_time AS DATE)                                           AS trip_date,
        EXTRACT(HOUR FROM tap_in_time)                                      AS hour_of_day,
        ISODOW(tap_in_time)                                                 AS day_of_week,

        -- trip duration (complete trips only)
        CASE WHEN has_tap_out
             THEN DATEDIFF('minute', tap_in_time, tap_out_time)
             ELSE NULL END                                                  AS duration_min,

        -- Haversine distance in km (complete trips with geo data)
        CASE WHEN has_tap_out
                  AND tap_in_lat  IS NOT NULL AND tap_in_lon  IS NOT NULL
                  AND tap_out_lat IS NOT NULL AND tap_out_lon IS NOT NULL
             THEN ROUND(
                2 * 6371 * ASIN(SQRT(
                    POWER(SIN(RADIANS(tap_out_lat - tap_in_lat) / 2), 2) +
                    COS(RADIANS(tap_in_lat)) * COS(RADIANS(tap_out_lat)) *
                    POWER(SIN(RADIANS(tap_out_lon - tap_in_lon) / 2), 2)
                )), 3)
             ELSE NULL END                                                  AS distance_km,

        -- convenience flag
        has_tap_out AND tap_in_lat IS NOT NULL AND tap_out_lat IS NOT NULL  AS is_complete_trip

    FROM joined
)

SELECT * FROM enriched
