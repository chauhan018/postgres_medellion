select
    p.patient_id,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    p.gender,
    p.blood_group,
    p.phone as patient_phone,
    p.address,
    p.city,
    p.admission_date,
    p.discharge_date,
    p.diagnosis,
    p.assigned_doctor_id,
    t.transaction_id,
    t.transaction_date,
    t.service_type,
    t.amount,
    t.payment_method,
    t.status as transaction_status
from {{ ref('stg_patient') }} p
left join {{ ref('stg_transaction') }} t
    on p.patient_id = t.patient_id