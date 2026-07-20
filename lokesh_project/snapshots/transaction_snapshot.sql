{% snapshot transaction_snapshot %}
 
{{
    config(
      target_schema='marts_lok',
      unique_key='transaction_id',
      strategy='check',
      check_cols=['status', 'payment_method', 'amount'],
    )
}}
 
select * from {{ ref('stg_transaction') }}
 
{% endsnapshot %} 