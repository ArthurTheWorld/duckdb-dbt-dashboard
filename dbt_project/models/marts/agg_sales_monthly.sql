{{ config(materialized='table') }}

SELECT
    DATE_TRUNC('month', purchase_date) AS month,
    COUNT(DISTINCT order_id) AS orders,
    SUM(total_value) AS revenue,
    AVG(total_value) AS avg_ticket
FROM {{ ref('fct_order_items') }}
WHERE order_status = 'delivered'
GROUP BY 1
ORDER BY 1
