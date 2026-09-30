{{ config(materialized='view') }}

SELECT
    seller_id,
    seller_city,
    seller_state
FROM {{ source('raw', 'olist_sellers_dataset') }}
WHERE seller_id IS NOT NULL
