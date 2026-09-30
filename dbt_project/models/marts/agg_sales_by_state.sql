{{ config(materialized='table') }}

SELECT
    customer_state,
    COUNT(DISTINCT order_id) AS orders,
    SUM(total_value) AS revenue,
    AVG(total_value) AS avg_ticket,
    AVG(review_score) AS avg_review_score
FROM {{ ref('fct_order_items') }}
WHERE order_status = 'delivered'
GROUP BY 1
ORDER BY revenue DESC
