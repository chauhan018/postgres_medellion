{{ config
    (
        materialized='incremental', 
        unique_key='transaction_id',
        post_hook= "DO $$ 
                BEGIN IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conrelid = '{{ this }}'::regclass AND contype='p') 
                THEN ALTER TABLE {{ this }} ADD PRIMARY KEY (transaction_id); 
                END IF; 
                END $$;"
    ) 
}}
select * from {{ source('raw_lok', 'transaction') }}
{% if is_incremental() %}
where load_ts > (select coalesce(max(load_ts), '1900-01-01'::timestamptz) from {{ this }})
{% endif %} 