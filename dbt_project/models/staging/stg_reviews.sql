{{ config(materialized='view') }}

SELECT
    review_id,
    order_id,
    review_score,
    review_creation_date
FROM {{ source('raw', 'olist_order_reviews_dataset') }}
WHERE review_id IS NOT NULL
