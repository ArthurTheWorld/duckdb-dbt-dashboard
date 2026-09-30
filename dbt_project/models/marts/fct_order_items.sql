{{ config(materialized='table') }}

SELECT
    i.order_id,
    i.order_item_id,
    i.product_id,
    p.category,
    i.seller_id,
    s.seller_state,
    o.customer_id,
    c.customer_state,
    o.purchase_date,
    o.order_status,
    i.price,
    i.freight_value,
    i.price + i.freight_value AS total_value,
    DATE_DIFF('day', o.purchase_date, CAST(o.order_delivered_customer_date AS DATE)) AS delivery_days,
    r.review_score
FROM {{ ref('stg_order_items') }} i
LEFT JOIN {{ ref('stg_orders') }} o ON i.order_id = o.order_id
LEFT JOIN {{ ref('stg_customers') }} c ON o.customer_id = c.customer_id
LEFT JOIN {{ ref('stg_products') }} p ON i.product_id = p.product_id
LEFT JOIN {{ ref('stg_sellers') }} s ON i.seller_id = s.seller_id
LEFT JOIN {{ ref('stg_reviews') }} r ON i.order_id = r.order_id
