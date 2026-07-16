{{
    config(
        materialized='incremental',
        unique_key='customer_id',
        incremental_strategy='merge',
        merge_exclude_columns=['dw_created_date', 'dw_created_by'],
        contract={'enforced': true},
        on_schema_change='fail',
        post_hook=[
        "ALTER TABLE {{ this }} ALTER COLUMN dq_flag SET DEFAULT 'valid'"
    ]
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
    '{{ run_started_at }}' as dw_created_date,
    '{{ run_started_at }}' as dw_modified_date,
    'dbt_stg_model' as dw_created_by,
    'dbt_stg_model' as dw_modified_by,
    '{{ invocation_id }}' as run_id,
    '{{ invocation_id }}' as batch_id
from {{ source('flipkart_raw', 'customers_raw') }}

{% if is_incremental() %}
    where dw_modified_date > (select max(dw_modified_date) from {{ this }})
{% endif %}