WITH source AS (
    SELECT * FROM {{ source('transjakarta', 'raw_transjakarta') }}
),

cleaned AS (
    SELECT
        transID                                   AS transaction_id,
        payCardID                                 AS card_id,
        LOWER(payCardBank)                        AS card_bank,
        payCardSex                                AS card_sex,
        CAST(payCardBirthDate AS INTEGER)         AS birth_year,
        2023 - CAST(payCardBirthDate AS INTEGER)  AS age_years,
        corridorID                                AS corridor_id,
        corridorName                              AS corridor_name,
        CAST(direction AS INTEGER)                AS direction,
        tapInStops                                AS tap_in_stop_id,
        tapInStopsName                            AS tap_in_stop_name,
        tapInStopsLat                             AS tap_in_lat,
        tapInStopsLon                             AS tap_in_lon,
        CAST(stopStartSeq AS INTEGER)             AS tap_in_seq,
        tapInTime                                 AS tap_in_time,
        tapOutStops                               AS tap_out_stop_id,
        tapOutStopsName                           AS tap_out_stop_name,
        tapOutStopsLat                            AS tap_out_lat,
        tapOutStopsLon                            AS tap_out_lon,
        CASE WHEN stopEndSeq IS NOT NULL
             THEN CAST(stopEndSeq AS INTEGER)
             ELSE NULL END                        AS tap_out_seq,
        tapOutTime                                AS tap_out_time,
        payAmount                                 AS pay_amount,
        tapOutStops IS NOT NULL                   AS has_tap_out
    FROM source
    WHERE corridorID IS NOT NULL
)

SELECT * FROM cleaned
