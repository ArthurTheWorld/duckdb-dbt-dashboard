{{ config(materialized='view') }}

SELECT
    order_id,
    customer_id,
    order_status,
    CAST(order_purchase_timestamp AS DATE) AS purchase_date,
    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date
FROM {{ source('raw', 'olist_orders_dataset') }}
WHERE order_id IS NOT NULL
