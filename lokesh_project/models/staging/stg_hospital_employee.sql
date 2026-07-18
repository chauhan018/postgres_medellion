{{ config(materialized='incremental', unique_key='employee_id',
   post_hook="DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = '{{ this }}'::regclass AND contype='p') THEN ALTER TABLE {{ this }} ADD PRIMARY KEY (employee_id); END IF; END $$;") }}

select * from {{ source('raw_lok', 'hospital_employee') }}
{% if is_incremental() %}
where load_ts > (select coalesce(max(load_ts), '1900-01-01'::timestamptz) from {{ this }})
{% endif %}
