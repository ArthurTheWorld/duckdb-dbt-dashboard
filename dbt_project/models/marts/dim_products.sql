{{ config(materialized='table') }}

SELECT
    p.product_id,
    p.category,
    p.product_weight_g,
    COUNT(f.order_id) AS times_sold,
    COALESCE(SUM(f.price), 0) AS total_revenue,
    AVG(f.review_score) AS avg_review_score
FROM {{ ref('stg_products') }} p
LEFT JOIN {{ ref('fct_order_items') }} f ON p.product_id = f.product_id
GROUP BY 1, 2, 3
