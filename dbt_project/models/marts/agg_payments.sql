{{ config(materialized='table') }}

SELECT
    p.payment_type,
    COUNT(*) AS payments,
    SUM(p.payment_value) AS total_value,
    AVG(p.payment_installments) AS avg_installments
FROM {{ ref('stg_payments') }} p
JOIN {{ ref('stg_orders') }} o ON p.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1
ORDER BY total_value DESC
