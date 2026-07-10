
-- Use the `ref` function to select from other models
{{ config(materialized='table') }}

select *
from {{ ref('main_table') }}
where id = 2
