{{ config(materialized='view') }}

SELECT
    customer_id,
    customer_unique_id,
    customer_city,
    customer_state
FROM {{ source('raw', 'olist_customers_dataset') }}
WHERE customer_id IS NOT NULL
