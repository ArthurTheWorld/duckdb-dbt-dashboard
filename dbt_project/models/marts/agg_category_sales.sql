{{ config(materialized='table') }}

SELECT
    category,
    COUNT(DISTINCT order_id) AS orders,
    SUM(price) AS revenue,
    AVG(price) AS avg_price,
    AVG(review_score) AS avg_review_score
FROM {{ ref('fct_order_items') }}
WHERE order_status = 'delivered'
GROUP BY 1
ORDER BY revenue DESC
