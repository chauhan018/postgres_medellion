select
    doctor_id as staff_id,
    'Doctor' as staff_type,
    first_name,
    last_name,
    department,
    specialization as role_or_specialization,
    phone,
    email,
    license_number,
    years_experience,
    consultation_fee,
    cast(null as date) as hire_date,
    cast(null as numeric) as salary,
    cast(null as text) as shift
from {{ ref('stg_doctors_record') }}

union all

select
    employee_id as staff_id,
    'Employee' as staff_type,
    first_name,
    last_name,
    department,
    role as role_or_specialization,
    phone,
    email,
    cast(null as text) as license_number,
    cast(null as integer) as years_experience,
    cast(null as numeric) as consultation_fee,
    hire_date,
    salary,
    shift
from {{ ref('stg_hospital_employee') }}
