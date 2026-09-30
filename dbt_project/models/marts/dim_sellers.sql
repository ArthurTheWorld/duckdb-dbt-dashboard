{{ config(materialized='table') }}

SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(DISTINCT f.order_id) AS number_of_orders,
    COALESCE(SUM(f.price), 0) AS total_revenue,
    AVG(f.review_score) AS avg_review_score
FROM {{ ref('stg_sellers') }} s
LEFT JOIN {{ ref('fct_order_items') }} f ON s.seller_id = f.seller_id
GROUP BY 1, 2, 3
