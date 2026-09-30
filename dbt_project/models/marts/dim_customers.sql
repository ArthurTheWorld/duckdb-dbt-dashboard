{{ config(materialized='table') }}

SELECT
    c.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    COUNT(DISTINCT f.order_id) AS number_of_orders,
    COALESCE(SUM(f.total_value), 0) AS lifetime_value,
    AVG(f.review_score) AS avg_review_score
FROM {{ ref('stg_customers') }} c
LEFT JOIN {{ ref('fct_order_items') }} f ON c.customer_id = f.customer_id
GROUP BY 1, 2, 3, 4
