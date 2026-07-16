{{
    config(
        materialized='incremental',
        unique_key='customer_id',
        incremental_strategy='merge',
        merge_exclude_columns=['dw_created_date'],
        contract={'enforced': true},
        on_schema_change='fail'
    )
}}

select
    customer_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    registration_date,
    customer_type,
    status,
    source_system,
    dq_flag,
    dw_created_date,
    dw_modified_date,
    dw_created_by,
    dw_modified_by,
    run_id,
    batch_id
from {{ source('flipkart_raw', 'customers_raw') }}

{% if is_incremental() %}
    where dw_modified_date > (select max(dw_modified_date) from {{ this }})
{% endif %}