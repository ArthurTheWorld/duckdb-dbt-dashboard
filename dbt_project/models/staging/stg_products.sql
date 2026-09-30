{{ config(materialized='view') }}

SELECT
    p.product_id,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    p.product_weight_g,
    p.product_photos_qty
FROM {{ source('raw', 'olist_products_dataset') }} p
LEFT JOIN {{ source('raw', 'product_category_name_translation') }} t
    ON p.product_category_name = t.product_category_name
WHERE p.product_id IS NOT NULL
