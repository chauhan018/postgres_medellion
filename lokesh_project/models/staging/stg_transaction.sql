select * from {{ source('raw_lok', 'transaction') }}
